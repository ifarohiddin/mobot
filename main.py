import logging
import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Configuration
API_TOKEN = "7876488844:AAFLtipD2pfKgfESPj1PSCWaF9NAqnzImZM"
MOVIES_FILE = "movies.json"  # Kinolarni saqlash uchun fayl nomi
CHANNELS_FILE = "channels.json"  # Kanallar ma'lumotlarini saqlash uchun fayl
ADMINS_FILE = "admins.json"  # Adminlar ma'lumotlarini saqlash uchun fayl

# State management classes
class EditMovieStates(StatesGroup):
    waiting_for_movie_code = State()
    waiting_for_new_data = State()

class EditChannelStates(StatesGroup):
    waiting_for_channel_code = State()
    waiting_for_new_data = State()

# Initialize bot and dispatcher with FSM storage
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Admin ID (faqat admin kino va kanal qo'shishi mumkin)
ADMIN_ID = 123456789  # Bu yerga adminning Telegram ID sini kiriting

def load_movies():
    """JSON fayldan kinolarni yuklash."""
    try:
        with open(MOVIES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_movies(movies):
    """JSON faylga yangi kinolarni saqlash."""
    with open(MOVIES_FILE, "w", encoding="utf-8") as f:
        json.dump(movies, f, indent=4, ensure_ascii=False)

def load_channels():
    """JSON fayldan kanallarni yuklash."""
    try:
        with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default channel
        default_channels = {
            "main": {"id": "-1001927486162", "url": "https://t.me/i_farohiddin", "name": "Asosiy kanal"}
        }
        save_channels(default_channels)
        return default_channels

def save_channels(channels):
    """JSON faylga yangi kanallarni saqlash."""
    with open(CHANNELS_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=4, ensure_ascii=False)

def load_admins():
    """JSON fayldan adminlarni yuklash."""
    try:
        with open(ADMINS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Default admin is the one configured above
        default_admins = [ADMIN_ID]
        save_admins(default_admins)
        return default_admins

def save_admins(admins):
    """JSON faylga adminlarni saqlash."""
    with open(ADMINS_FILE, "w", encoding="utf-8") as f:
        json.dump(admins, f, indent=4, ensure_ascii=False)

def is_admin(user_id: int) -> bool:
    """Foydalanuvchi admin ekanligini tekshirish."""
    return user_id in ADMINS

# Bot ishga tushganda kinolarni, kanallarni va adminlarni yuklash
MOVIE_STORAGE = load_movies()
CHANNELS = load_channels()
ADMINS = load_admins()

async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed to all required channels."""
    # Admin uchun kanalga a'zo bo'lish shart emas
    if is_admin(user_id):
        return True
    
    for channel_key, channel_info in CHANNELS.items():
        try:
            member = await bot.get_chat_member(channel_info["id"], user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        except Exception as e:
            logger.error(f"Error checking subscription for channel {channel_key}: {e}")
            return False
    return True

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with subscription buttons for all channels."""
    keyboard = []
    for channel_key, channel_info in CHANNELS.items():
        keyboard.append([
            InlineKeyboardButton(
                text=f"➡️ {channel_info['name']}ga o'tish",
                url=channel_info["url"]
            )
        ])
    
    keyboard.append([
        InlineKeyboardButton(
            text="✅ Obunani tekshirish",
            callback_data="check_subs"
        )
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with admin buttons."""
    keyboard = [
        [
            InlineKeyboardButton(
                text="➕ Kino qo'shish",
                callback_data="add_movie_start"
            )
        ],
        [
            InlineKeyboardButton(
                text="✏️ Kino tahrirlash",
                callback_data="edit_movie_start"
            ),
            InlineKeyboardButton(
                text="🗑️ Kino o'chirish",
                callback_data="remove_movie_start"
            )
        ],
        [
            InlineKeyboardButton(
                text="➕ Kanal qo'shish",
                callback_data="add_channel_start"
            ),
            InlineKeyboardButton(
                text="✏️ Kanal tahrirlash",
                callback_data="edit_channel_start"
            )
        ],
        [
            InlineKeyboardButton(
                text="❌ Kanal o'chirish",
                callback_data="remove_channel_start"
            ),
            InlineKeyboardButton(
                text="📋 Kanallar ro'yxati",
                callback_data="list_channels"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Kinolar ro'yxati",
                callback_data="list_movies"
            )
        ]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """Handle /start command."""
    try:
        global ADMINS
        user_id = message.from_user.id
        
        # Admin avtomatik aniqlanishi
        if user_id == ADMIN_ID and user_id not in ADMINS:
            ADMINS.append(user_id)
            save_admins(ADMINS)
            await message.answer(f"✅ Siz admin sifatida avtomatik qo'shildingiz!\n\nAdmin ID: {user_id}")
        
        # Admin menu ko'rsatish
        if is_admin(user_id):
            await message.answer(
                f"👑 Xush kelibsiz, Admin!\n\nQuyidagi amallardan birini tanlang:",
                reply_markup=get_admin_keyboard()
            )
            return
        
        # Normal foydalanuvchilar uchun
        is_subscribed = await check_subscription(user_id)
        
        if not is_subscribed:
            keyboard = get_subscription_keyboard()
            channel_list = "\n".join([f"- {info['name']}" for key, info in CHANNELS.items()])
            await message.answer(
                f"⛔ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:\n\n{channel_list}",
                reply_markup=keyboard
            )
        else:
            # Mavjud kinolar ro'yxatini tayyorlash
            movie_list = "\n".join([f"{code} - {info['name']}" for code, info in MOVIE_STORAGE.items()])
            
            await message.answer(
                f"✅ Xush kelibsiz! Kino kodini yuboring:\n"
            )
    except Exception as e:
        logger.error(f"Error in start handler: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@dp.callback_query(F.data == "check_subs")
async def check_subscriptions(call: types.CallbackQuery):
    """Handle subscription check callback."""
    try:
        is_subscribed = await check_subscription(call.from_user.id)
        
        if not is_subscribed:
            channel_list = "\n".join([f"- {info['name']}" for key, info in CHANNELS.items()])
            await call.answer(f"⛔ Siz hali barcha kanallarga a'zo bo'lmagansiz!", show_alert=True)
        else:
            # Mavjud kinolar ro'yxatini tayyorlash
            movie_list = "\n".join([f"{code} - {info['name']}" for code, info in MOVIE_STORAGE.items()])
            
            await call.message.edit_text(
                f"✅ Obuna tasdiqlandi!\n\nKino kodini yuboring:\n"
            )
    except Exception as e:
        logger.error(f"Error in subscription check: {e}")
        await call.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.", show_alert=True)

# Admin callback handlerlar
@dp.callback_query(F.data == "add_movie_start")
async def add_movie_start(call: types.CallbackQuery):
    """Start adding a movie process."""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!", show_alert=True)
        return
    
    await call.message.edit_text(
        "🎬 Yangi kino qo'shish uchun quyidagi formatda ma'lumotlarni kiriting:\n\n"
        "`kod|https://t.me/link|Kino nomi`\n\n"
        "Masalan: `123|https://t.me/mykino_server/5|Avatar 2`",
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data == "edit_movie_start")
async def edit_movie_start(call: types.CallbackQuery, state: FSMContext):
    """Start editing a movie process."""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!", show_alert=True)
        return
    
    movies = load_movies()
    if not movies:
        await call.message.edit_text(
            "ℹ️ Hozircha hech qanday kino qo'shilmagan. Avval kino qo'shing.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin_menu")
            ]])
        )
        await call.answer()
        return
    
    movie_list = "\n".join([f"- {code}: {info['name']}" for code, info in movies.items()])
    
    await state.set_state(EditMovieStates.waiting_for_movie_code)
    
    await call.message.edit_text(
        f"✏️ Qaysi kinoni tahrirlash kerak?\n\nMavjud kinolar:\n{movie_list}\n\n"
        "Tahrirlash uchun kino kodini yuboring:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="back_to_admin_menu")
        ]])
    )
    await call.answer()

@dp.message(EditMovieStates.waiting_for_movie_code)
async def process_movie_code_for_edit(message: types.Message, state: FSMContext):
    """Process movie code for editing."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!")
        await state.clear()
        return
    
    movies = load_movies()
    movie_code = message.text.strip()
    
    if movie_code not in movies:
        await message.answer(
            f"❌ '{movie_code}' kodi bilan kino topilmadi! Iltimos, to'g'ri kino kodini yuboring:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="back_to_admin_menu")
            ]])
        )
        return
    
    movie_info = movies[movie_code]
    
    await state.update_data(movie_code=movie_code)
    await state.set_state(EditMovieStates.waiting_for_new_data)
    
    await message.answer(
        f"✏️ '{movie_code}' kodli kino tahrirlash uchun ma'lumotlarni yuboring:\n\n"
        f"Hozirgi ma'lumotlar:\n"
        f"- Kino nomi: {movie_info['name']}\n"
        f"- URL: {movie_info['url']}\n\n"
        f"Yangi ma'lumotlarni quyidagi formatda yuboring:\n"
        f"`https://t.me/link|Yangi kino nomi`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="back_to_admin_menu")
        ]])
    )

@dp.message(EditMovieStates.waiting_for_new_data)
async def process_new_movie_data(message: types.Message, state: FSMContext):
    """Process new movie data for editing."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!")
        await state.clear()
        return
    
    data = await state.get_data()
    movie_code = data.get("movie_code")
    
    try:
        new_url, new_name = message.text.split("|")
        new_url = new_url.strip()
        new_name = new_name.strip()
        
        # Fayldan mavjud kinolarni yuklash va yangilash
        movies = load_movies()
        old_name = movies[movie_code]["name"]
        movies[movie_code] = {"url": new_url, "name": new_name}
        save_movies(movies)
        
        # Global o'zgaruvchini ham yangilash
        global MOVIE_STORAGE
        MOVIE_STORAGE = movies
        
        await message.answer(
            f"✅ Kino tahrirlandi!\n\n"
            f"🎬 Kino kodi: {movie_code}\n"
            f"🔄 Eski nomi: {old_name}\n"
            f"✏️ Yangi nomi: {new_name}",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error editing movie: {e}")
        await message.answer(
            "❌ Tahrirlashda xatolik yuz berdi. Format to'g'riligini tekshiring.\n\n"
            "To'g'ri format: `https://t.me/link|Yangi kino nomi`",
            parse_mode="Markdown"
        )
    
    await state.clear()

@dp.callback_query(F.data == "remove_movie_start")
async def remove_movie_start(call: types.CallbackQuery):
    """Start removing a movie process."""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!", show_alert=True)
        return
    
    movies = load_movies()
    if not movies:
        await call.message.edit_text(
            "ℹ️ Hozircha hech qanday kino qo'shilmagan.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin_menu")
            ]])
        )
        await call.answer()
        return
    
    movie_list = "\n".join([f"- {code}: {info['name']}" for code, info in movies.items()])
    
    await call.message.edit_text(
        f"🗑️ Qaysi kinoni o'chirish kerak?\n\nMavjud kinolar:\n{movie_list}\n\n"
        "O'chirish uchun kino kodini yuboring:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="back_to_admin_menu")
        ]])
    )
    await call.answer()

@dp.callback_query(F.data == "add_channel_start")
async def add_channel_start(call: types.CallbackQuery):
    """Start adding a channel process."""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!", show_alert=True)
        return
    
    await call.message.edit_text(
        "📢 Yangi kanal qo'shish uchun quyidagi formatda ma'lumotlarni kiriting:\n\n"
        "`kod|-100123456789|https://t.me/kanal|Kanal nomi`\n\n"
        "Masalan: `test|-1001234567890|https://t.me/test_channel|Test Kanal`",
        parse_mode="Markdown"
    )
    await call.answer()

@dp.callback_query(F.data == "edit_channel_start")
async def edit_channel_start(call: types.CallbackQuery, state: FSMContext):
    """Start editing a channel process."""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!", show_alert=True)
        return
    
    channels = load_channels()
    if not channels:
        await call.message.edit_text(
            "ℹ️ Hozircha hech qanday kanal qo'shilmagan. Avval kanal qo'shing.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin_menu")
            ]])
        )
        await call.answer()
        return
    
    channel_list = "\n".join([f"- {code}: {info['name']}" for code, info in channels.items()])
    
    await state.set_state(EditChannelStates.waiting_for_channel_code)
    
    await call.message.edit_text(
        f"✏️ Qaysi kanalni tahrirlash kerak?\n\nMavjud kanallar:\n{channel_list}\n\n"
        "Tahrirlash uchun kanal kodini yuboring:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="back_to_admin_menu")
        ]])
    )
    await call.answer()

@dp.message(EditChannelStates.waiting_for_channel_code)
async def process_channel_code_for_edit(message: types.Message, state: FSMContext):
    """Process channel code for editing."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!")
        await state.clear()
        return
    
    channels = load_channels()
    channel_code = message.text.strip()
    
    if channel_code not in channels:
        await message.answer(
            f"❌ '{channel_code}' kodi bilan kanal topilmadi! Iltimos, to'g'ri kanal kodini yuboring:",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="back_to_admin_menu")
            ]])
        )
        return
    
    channel_info = channels[channel_code]
    
    await state.update_data(channel_code=channel_code)
    await state.set_state(EditChannelStates.waiting_for_new_data)
    
    await message.answer(
        f"✏️ '{channel_code}' kodli kanalni tahrirlash uchun ma'lumotlarni yuboring:\n\n"
        f"Hozirgi ma'lumotlar:\n"
        f"- Kanal nomi: {channel_info['name']}\n"
        f"- Kanal ID: {channel_info['id']}\n"
        f"- URL: {channel_info['url']}\n\n"
        f"Yangi ma'lumotlarni quyidagi formatda yuboring:\n"
        f"`-100123456789|https://t.me/kanal|Yangi kanal nomi`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="back_to_admin_menu")
        ]])
    )

@dp.message(EditChannelStates.waiting_for_new_data)
async def process_new_channel_data(message: types.Message, state: FSMContext):
    """Process new channel data for editing."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!")
        await state.clear()
        return
    
    data = await state.get_data()
    channel_code = data.get("channel_code")
    
    try:
        new_id, new_url, new_name = message.text.split("|")
        new_id = new_id.strip()
        new_url = new_url.strip()
        new_name = new_name.strip()
        
        # Fayldan mavjud kanallarni yuklash va yangilash
        channels = load_channels()
        old_name = channels[channel_code]["name"]
        channels[channel_code] = {"id": new_id, "url": new_url, "name": new_name}
        save_channels(channels)
        
        # Global o'zgaruvchini ham yangilash
        global CHANNELS
        CHANNELS = channels
        
        await message.answer(
            f"✅ Kanal tahrirlandi!\n\n"
            f"📢 Kanal kodi: {channel_code}\n"
            f"🔄 Eski nomi: {old_name}\n"
            f"✏️ Yangi nomi: {new_name}",
            reply_markup=get_admin_keyboard()
        )
    except Exception as e:
        logger.error(f"Error editing channel: {e}")
        await message.answer(
            "❌ Tahrirlashda xatolik yuz berdi. Format to'g'riligini tekshiring.\n\n"
            "To'g'ri format: `-100123456789|https://t.me/kanal|Yangi kanal nomi`",
            parse_mode="Markdown"
        )
    
    await state.clear()

@dp.callback_query(F.data == "remove_channel_start")
async def remove_channel_start(call: types.CallbackQuery):
    """Start removing a channel process."""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!", show_alert=True)
        return
    
    channels = load_channels()
    channel_list = "\n".join([f"- {code}: {info['name']}" for code, info in channels.items()])
    
    await call.message.edit_text(
        f"🗑 Kanal o'chirish uchun kanal kodini kiriting.\n\nMavjud kanallar:\n{channel_list}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Bekor qilish", callback_data="back_to_admin_menu")
        ]])
    )
    await call.answer()

@dp.callback_query(F.data == "list_channels")
async def list_channels_callback(call: types.CallbackQuery):
    """List all channels via callback."""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!", show_alert=True)
        return
    
    channels = load_channels()
    if not channels:
        await call.message.edit_text("ℹ️ Hozircha hech qanday kanal qo'shilmagan.")
        await call.answer()
        return
    
    channel_list = "\n\n".join([f"📢 {info['name']}\nKod: {code}\nID: {info['id']}\nURL: {info['url']}" 
                              for code, info in channels.items()])
    
    await call.message.edit_text(
        f"📋 Mavjud kanallar ro'yxati:\n\n{channel_list}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin_menu")
        ]])
    )
    await call.answer()

@dp.callback_query(F.data == "list_movies")
async def list_movies_callback(call: types.CallbackQuery):
    """List all movies via callback."""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!", show_alert=True)
        return
    
    movies = load_movies()
    if not movies:
        await call.message.edit_text("ℹ️ Hozircha hech qanday kino qo'shilmagan.")
        await call.answer()
        return
    
    movie_list = "\n\n".join([f"🎬 {info['name']}\nKod: {code}\nURL: {info['url']}" 
                            for code, info in movies.items()])
    
    await call.message.edit_text(
        f"📋 Mavjud kinolar ro'yxati:\n\n{movie_list}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="back_to_admin_menu")
        ]])
    )
    await call.answer()

@dp.callback_query(F.data == "back_to_admin_menu")
async def back_to_admin_menu(call: types.CallbackQuery, state: FSMContext):
    """Go back to admin menu."""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda bu amalni bajarish huquqi yo'q!", show_alert=True)
        return
    
    # State ni tozalash
    await state.clear()
    
    await call.message.edit_text(
        "👑 Admin paneli\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=get_admin_keyboard()
    )
    await call.answer()

@dp.message()
async def handle_message(message: types.Message, state: FSMContext):
    """Handle all messages including movie requests and admin commands."""
    try:
        global MOVIE_STORAGE, CHANNELS  # Declare all globals at the beginning
        
        # Agar foydalanuvchi biror state ichida bo'lsa, bu habarga javob bermaymiz
        current_state = await state.get_state()
        if current_state is not None:
            return
        
        user_id = message.from_user.id
        
        # Admin uchun maxsus xabarlarni qayta ishlash
        if is_admin(user_id):
            text = message.text.strip()
            
            # Yangi kino qo'shish
            if "|" in text and text.count("|") == 2:
                try:
                    code, url, name = text.split("|")
                    
                    # Fayldan mavjud kinolarni yuklash va yangilash
                    movies = load_movies()
                    movies[code] = {"url": url, "name": name}
                    save_movies(movies)
                    
                    # Global o'zgaruvchini ham yangilash
                    MOVIE_STORAGE = movies
                    
                    await message.answer(
                        f"✅ Kino qo'shildi!\n\n🎬 {name} ({code})",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                except Exception as e:
                    logger.error(f"Error adding movie: {e}")
                    await message.answer("❌ Kino qo'shishda xatolik yuz berdi. Format to'g'riligini tekshiring.")
                    return
            
            # Yangi kanal qo'shish
            elif "|" in text and text.count("|") == 3:
                try:
                    code, channel_id, url, name = text.split("|")
                    
                    # Fayldan mavjud kanallarni yuklash va yangilash
                    channels = load_channels()
                    channels[code] = {"id": channel_id, "url": url, "name": name}
                    save_channels(channels)
                    
                    # Global o'zgaruvchini ham yangilash
                    CHANNELS = channels
                    
                    await message.answer(
                        f"✅ Kanal qo'shildi!\n\n📢 {name} ({code})",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                except Exception as e:
                    logger.error(f"Error adding channel: {e}")
                    await message.answer("❌ Kanal qo'shishda xatolik yuz berdi. Format to'g'riligini tekshiring.")
                    return
            
            # Kanal o'chirish
            elif text in load_channels():
                try:
                    channels = load_channels()
                    channel_name = channels[text]["name"]
                    del channels[text]
                    save_channels(channels)
                    
                    # Global o'zgaruvchini ham yangilash
                    CHANNELS = channels
                    
                    await message.answer(
                        f"✅ Kanal o'chirildi!\n\n📢 {channel_name} ({text})",
                        reply_markup=get_admin_keyboard()
                    )
                    return
                except Exception as e:
                    logger.error(f"Error removing channel: {e}")
                    await message.answer("❌ Kanal o'chirishda xatolik yuz berdi.")
                    return
        
        # Normal foydalanuvchilar va adminlar uchun kino so'rovlarini qayta ishlash
        is_subscribed = await check_subscription(user_id)
        
        if not is_subscribed:
            keyboard = get_subscription_keyboard()
            channel_list = "\n".join([f"- {info['name']}" for key, info in CHANNELS.items()])
            await message.answer(
                f"⛔ Botdan foydalanish uchun quyidagi kanallarga a'zo bo'ling:\n\n{channel_list}",
                reply_markup=keyboard
            )
            return

        movie_code = message.text.strip()

        # JSON dan yangilangan kinolarni yuklash
        MOVIE_STORAGE = load_movies()

        if movie_code in MOVIE_STORAGE:
            movie_info = MOVIE_STORAGE[movie_code]
            await message.answer_video(
                video=movie_info["url"],
                caption=f"Kino kodi: {movie_code}\nNomi: {movie_info['name']}"
            )
        elif not is_admin(user_id):  # Admin uchun xabar chiqarilmaydi, chunki u menu uchun boshqa buyruqlar yuborishi mumkin
            movie_list = "\n".join([f"{code} - {info['name']}" for code, info in MOVIE_STORAGE.items()])
            await message.answer(f"❌ Noto'g'ri kino kodi kiritildi!\n\n")
    except Exception as e:
        logger.error(f"Error in message handler: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@dp.message(Command("add_movie"))
async def add_movie_command(message: types.Message):
    """Admin kinoni qo'shish uchun buyruq."""
    global MOVIE_STORAGE  # Declare global at the beginning
    
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu buyruqdan foydalanish huquqi yo'q!")
        return

    try:
        # Kino qo'shish formati: /add_movie 4|https://t.me/mykino_server/5|Yangi Kino
        data = message.text.split(" ", 1)[1]
        code, url, name = data.split("|")

        # Fayldan mavjud kinolarni yuklash va yangilash
        movies = load_movies()
        movies[code] = {"url": url, "name": name}
        save_movies(movies)
        
        # Global o'zgaruvchini ham yangilash
        MOVIE_STORAGE = movies

        await message.answer(f"✅ Kino qo'shildi!\n\n🎬 {name} ({code})")
    except Exception as e:
        await message.answer("❌ Format noto'g'ri! Quyidagi ko'rinishda kiriting:\n\n`/add_movie 4|https://t.me/link|Yangi Kino`", parse_mode="Markdown")

@dp.message(Command("add_channel"))
async def add_channel_command(message: types.Message):
    """Admin kanal qo'shish uchun buyruq."""
    global CHANNELS  # Declare global at the beginning
    
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu buyruqdan foydalanish huquqi yo'q!")
        return

    try:
        # Kanal qo'shish formati: /add_channel kanal_kodi|-100123456789|https://t.me/kanal|Kanal Nomi
        data = message.text.split(" ", 1)[1]
        code, channel_id, url, name = data.split("|")

        # Fayldan mavjud kanallarni yuklash va yangilash
        channels = load_channels()
        channels[code] = {"id": channel_id, "url": url, "name": name}
        save_channels(channels)

        # Global CHANNELS o'zgaruvchisini yangilash
        CHANNELS = channels

        await message.answer(f"✅ Kanal qo'shildi!\n\n📢 {name} ({code})")
    except Exception as e:
        await message.answer("❌ Format noto'g'ri! Quyidagi ko'rinishda kiriting:\n\n`/add_channel kanal_kodi|-100123456789|https://t.me/kanal|Kanal Nomi`", parse_mode="Markdown")

@dp.message(Command("remove_channel"))
async def remove_channel_command(message: types.Message):
    """Admin kanalni o'chirish uchun buyruq."""
    global CHANNELS  # Declare global at the beginning
    
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu buyruqdan foydalanish huquqi yo'q!")
        return

    try:
        # Kanal o'chirish formati: /remove_channel kanal_kodi
        channel_code = message.text.split(" ", 1)[1].strip()

        # Fayldan mavjud kanallarni yuklash
        channels = load_channels()
        
        if channel_code in channels:
            channel_name = channels[channel_code]["name"]
            del channels[channel_code]
            save_channels(channels)
            
            # Global CHANNELS o'zgaruvchisini yangilash
            CHANNELS = channels
            
            await message.answer(f"✅ Kanal o'chirildi!\n\n📢 {channel_name} ({channel_code})")
        else:
            await message.answer(f"❌ '{channel_code}' kodi bilan kanal topilmadi!")
    except Exception as e:
        await message.answer("❌ Format noto'g'ri! Quyidagi ko'rinishda kiriting:\n\n`/remove_channel kanal_kodi`", parse_mode="Markdown")

@dp.message(Command("list_channels"))
async def list_channels_command(message: types.Message):
    """Admin uchun mavjud kanallar ro'yxatini ko'rsatish."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu buyruqdan foydalanish huquqi yo'q!")
        return
    
    channels = load_channels()
    if not channels:
        await message.answer("ℹ️ Hozircha hech qanday kanal qo'shilmagan.")
        return
    
    channel_list = "\n\n".join([f"📢 {info['name']}\nKod: {code}\nID: {info['id']}\nURL: {info['url']}" 
                              for code, info in channels.items()])
    
    await message.answer(f"📋 Mavjud kanallar ro'yxati:\n\n{channel_list}")

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    """Admin panelga kirish uchun buyruq."""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Sizda bu buyruqdan foydalanish huquqi yo'q!")
        return
    
    await message.answer(
        "👑 Admin paneli\n\nQuyidagi amallardan birini tanlang:",
        reply_markup=get_admin_keyboard()
    )

async def main():
    """Main function to run the bot."""
    try:
        logging.info("Starting bot...")
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"Critical error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
