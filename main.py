from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.fsm.state import State, StatesGroup
from movie_request import request_movie, MovieStates
from send_movie import send_movie
from admin_panel import add_movie, edit_movie, delete_movie, set_channel, delete_channel, edit_channel
from database import init_db
from aiogram.filters import Command
from check_user import check_membership, get_channels_from_db
from aiogram.fsm.context import FSMContext
from typing import Union
import os
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse
import asyncio

load_dotenv()

# Ma'lumotlar bazasini ishga tushirish
try:
    init_db()
except Exception as e:
    print(f"Database initialization failed: {e}")
    raise

bot = Bot(token=os.getenv("BOT_TOKEN"))
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Global o‘zgaruvchi sifatida kanal ID’sini saqlash
CHANNEL_ID = os.getenv("CHANNEL_ID", "@DefaultChannel")  # .env dan olish mumkin

# Admin ID’larini .env dan olish
admin_ids_str = os.getenv("ADMIN_IDS", "5358180855")  # Standart qiymat sifatida bitta ID
ADMINS = [int(id.strip()) for id in admin_ids_str.split(',')]  # Vergul bilan ajratilgan ID’lar ro‘yxatini olish

# Yangi davlatlar (states) aniqlash
class AdminStates(StatesGroup):
    waiting_for_movie_link = State()
    waiting_for_movie_name = State()
    waiting_for_movie_id = State()  # Kino ID’si uchun (tahrirlash/o‘chirish)
    waiting_for_movie_new_value = State()  # Yangi qiymat uchun (tahrirlash)
    waiting_for_channel_name = State()  # Kanal nomi uchun
    waiting_for_channel_id = State()  # Kanal ID’si uchun
    waiting_for_channel_link = State()  # Kanal linki uchun
    waiting_for_delete_channel = State()
    waiting_for_edit_channel = State()
    waiting_for_delete_movie = State()  # Kino o‘chirish uchun yangi davlat

class UserStates(StatesGroup):
    waiting_for_movie_id = State()  # Foydalanuvchi uchun kino ID’si

# Kinolar ro‘yxatini olish funksiyasi
async def get_movies_list(bot: Bot, user_id: int):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "Ma'lumotlar bazasi ulanishi topilmadi!"

    url = urlparse(db_url)
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        sslmode='require'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, link FROM movies")
    movies = cursor.fetchall()
    conn.close()

    if not movies:
        return "Hozircha hech qanday kino mavjud emas!"

    response = "🎥 *Kinolar Ro‘yxati:*\n"
    for movie in movies:
        response += f"📌 ID: `{movie[0]}` | Nom: *{movie[1]}* | Link: `{movie[2]}`\n"
    return response

# Reklamma kanallarni olish funksiyasi (ma'lumotlar bazasidan)
async def get_advertisement_channels_list(bot: Bot) -> list:
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return []

    url = urlparse(db_url)
    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port,
        sslmode='require'
    )
    cursor = conn.cursor()
    cursor.execute("SELECT name, id, link FROM advertisement_channels")
    channels = cursor.fetchall()
    conn.close()

    return channels  # Hamma kanal ma'lumotlarini (nom, ID, link) qaytaradi

# /start komandasiga javob (foydalanuvchi uchun salomlashish va ma'lumotlar bazasidagi reklamma kanallari ro‘yxati)
@dp.message(Command(commands=["start"]))
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id

    if user_id in ADMINS:
        # Admin uchun estetik inline button'lar
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(text="🎬 Kino Qo'shish", callback_data="add_movie"),
                types.InlineKeyboardButton(text="✏️ Kino Tahrirlash", callback_data="edit_movie")
            ],
            [
                types.InlineKeyboardButton(text="🗑️ Kino O'chirish", callback_data="delete_movie"),
                types.InlineKeyboardButton(text="👀 Kinolar Ro‘yxati", callback_data="view_movies")
            ],
            [
                types.InlineKeyboardButton(text="🌐 Kanal Qo'shish", callback_data="set_channel"),
                types.InlineKeyboardButton(text="🗑️ Kanal O'chirish", callback_data="delete_channel")
            ],
            [
                types.InlineKeyboardButton(text="✏️ Kanal Tahrirlash", callback_data="edit_channel"),
                types.InlineKeyboardButton(text="🌐 Kanallar Ro‘yxati", callback_data="view_channels")
            ]
        ])
<<<<<<< HEAD
        await message.answer("*Salom, Admin! Quyidagi opsiyalardan birini tanlang:*\n\nBotim bilan ishlayotganingizdan xursandman! 🎉", reply_markup=keyboard, parse_mode="Markdown")
    else:
        # Oddiy foydalanuvchi uchun salomlashish va ma'lumotlar bazasidagi reklamma kanallari ro‘yxati
        await message.answer("*Salom, hurmatli foydalanuvchi! Men kino botiman. Avval reklamma kanallarga a'zo bo'ling!*\n\nBotim bilan tanishganingizdan xursandman! 🌟", parse_mode="Markdown")
        channels = await get_advertisement_channels_list(bot)
        if not channels:
            await message.answer("*⚠️ Hozircha hech qanday reklamma kanal mavjud emas!*\n\nAdmin bilan bog‘laning yoki kanallarni qo‘shing.", parse_mode="Markdown")
=======
    
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
>>>>>>> debfd7ef3f458ec647871567d00ee63d1ed25fbc
            return

        # Foydalanuvchining a’zoligini tekshirish
        channel_ids = [channel[1] for channel in channels]  # Faqat ID’lar ro‘yxatini olish
        membership_results = await asyncio.gather(*[check_membership(message, bot, None, channel_id) for channel_id in channel_ids])
        non_member_channels = [channel for i, channel in enumerate(channels) if not membership_results[i]]

<<<<<<< HEAD
        if not non_member_channels:
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🌐 Kanallar Ro‘yxati", callback_data="view_channels")]
            ])
            await message.answer("*✅ Siz barcha zarur reklamma kanallarga a'zo ekansiz! Kino so‘rov qilish uchun kino ID’sini kiriting:*\n\nMenga yordam berish uchun kanalga a'zo bo‘ling! 🎥", reply_markup=keyboard, parse_mode="Markdown")
            await state.set_state(UserStates.waiting_for_movie_id)  # Foydalanuvchi uchun kino ID’si davlati
=======
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
>>>>>>> debfd7ef3f458ec647871567d00ee63d1ed25fbc
        else:
            # Faqat a’zo bo‘lmagan reklamma kanallarni button’lar bilan ko‘rsatish
            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text=f"📋 Kanal: {channel[0]}", url=channel[2] if channel[2].startswith("https://t.me/") else f"https://t.me/{channel[1].replace('@', '') if channel[1].startswith('@') else channel[1]}")]
                for channel in non_member_channels
            ] + [[types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_membership")]])
            await message.answer("*Iltimos, quyidagi reklamma kanallarga a'zo bo'ling, keyin “Tekshirish” tugmasini bosing!*\n\nKanalga a'zo bo‘lganingizdan keyin men bilan davom eting! 🚀", reply_markup=keyboard, parse_mode="Markdown")

# Callback handler’lar (foydalanuvchi uchun tekshirish)
@dp.callback_query(lambda c: c.data == "check_membership")
async def process_check_membership(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    user_id = callback_query.from_user.id
    message = callback_query.message

    # Ma'lumotlar bazasidan reklamma kanallarni olish
    channels = await get_advertisement_channels_list(bot)
    if not channels:
        await message.answer("*⚠️ Hozircha hech qanday reklamma kanal mavjud emas!*\n\nAdmin bilan bog‘laning yoki kanallarni qo‘shing.", parse_mode="Markdown")
        return

    # Asinxron chaqiruvlarni to‘g‘ri boshqarish
    channel_ids = [channel[1] for channel in channels]  # Faqat ID’lar ro‘yxatini olish
    membership_results = await asyncio.gather(*[check_membership(message, bot, None, channel_id) for channel_id in channel_ids])
    if all(membership_results):
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🌐 Kanallar Ro‘yxati", callback_data="view_channels")]
        ])
        await message.answer("*✅ Siz barcha zarur reklamma kanallarga a'zo ekansiz! Kino so‘rov qilish uchun kino ID’sini kiriting:*\n\nMenga yordam berish uchun kanalga a'zo bo‘ling! 🎥", reply_markup=keyboard, parse_mode="Markdown")
        await state.set_state(UserStates.waiting_for_movie_id)  # Foydalanuvchi uchun kino ID’si davlati
    else:
        # Faqat a’zo bo‘lmagan reklamma kanallarni button’lar bilan qayta ko‘rsatish
        non_member_channels = [channel for i, channel in enumerate(channels) if not membership_results[i]]
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=f"📋 Kanal: {channel[0]}", url=channel[2] if channel[2].startswith("https://t.me/") else f"https://t.me/{channel[1].replace('@', '') if channel[1].startswith('@') else channel[1]}")]
            for channel in non_member_channels
        ] + [[types.InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_membership")]])
        await message.answer("*❌ Siz hali barcha reklamma kanallarga a'zo emassiz! Iltimos, quyidagi kanallarga a'zo bo'ling, keyin qayta tekshiring!*\n\nKanalga a'zo bo‘lganingizdan keyin men bilan davom eting! 🚀", reply_markup=keyboard, parse_mode="Markdown")

# Callback handler'lar admin uchun
@dp.callback_query(lambda c: c.data == "add_movie")
async def process_add_movie(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "*🎬 Kino manzilini (boshqa kanaldan link sifatida) kiriting:*\n\nMasalan: *https://t.me/example_channel/123*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_movie_link)

@dp.callback_query(lambda c: c.data == "edit_movie")
async def process_edit_movie(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "*✏️ Kino ID’sini kiriting:*\n\nMasalan: *1*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_movie_id)

@dp.callback_query(lambda c: c.data == "delete_movie")
async def process_delete_movie(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "*🗑️ O'chirish uchun kino ID’sini kiriting:*\n\nMasalan: *1*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_delete_movie)

@dp.callback_query(lambda c: c.data == "set_channel")
async def process_set_channel(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "*🌐 Kanal nomini kiriting:*\n\nMasalan: *Kino PRIME*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_channel_name)

@dp.callback_query(lambda c: c.data == "delete_channel")
async def process_delete_channel(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "*🗑️ O'chirish uchun kanal ID’sini kiriting:*\n\nMasalan: *@example_channel* yoki *-1001234567890*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_delete_channel)

@dp.callback_query(lambda c: c.data == "edit_channel")
async def process_edit_channel(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "*✏️ Kanal ID va yangi kanal ID’sini kiriting (format: <eski_ID> <yangi_ID>):*\n\nMasalan: *@old_channel @new_channel*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_edit_channel)

@dp.callback_query(lambda c: c.data == "view_movies")
async def process_view_movies(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    movies_list = await get_movies_list(bot, callback_query.from_user.id)
    await bot.send_message(callback_query.from_user.id, movies_list, parse_mode="Markdown")

@dp.callback_query(lambda c: c.data == "view_channels")
async def process_view_channels(callback_query: types.CallbackQuery, state: FSMContext):
    await bot.answer_callback_query(callback_query.id)
    channels_list = await get_advertisement_channels_list(bot)
    response = "🌐 *Reklamma Kanallar Ro‘yxati:*\n" + "\n".join([f"📋 Nom: *{channel[0]}* | ID: `{channel[1]}` | Link: *{channel[2]}*" for channel in channels_list])
    await bot.send_message(callback_query.from_user.id, response, parse_mode="Markdown")

# Admin uchun yangi handler'lar
@dp.message(AdminStates.waiting_for_channel_name, lambda message: message.from_user.id in ADMINS)
async def handle_channel_name(message: Message, state: FSMContext):
    channel_name = message.text
    if not channel_name:
        await message.answer("*❌ Iltimos, to‘g‘ri kanal nomini kiriting!*\n\nMasalan: *Kino PRIME*", parse_mode="Markdown")
        return
    await state.update_data(channel_name=channel_name)
    await message.answer("*🌐 Kanal ID’sini kiriting:*\n\nMasalan: *@example_channel* yoki *-1001234567890*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_channel_id)

@dp.message(AdminStates.waiting_for_channel_id, lambda message: message.from_user.id in ADMINS)
async def handle_channel_id(message: Message, state: FSMContext):
    channel_id = message.text
    if not (channel_id.startswith('@') or channel_id.startswith('-100')):
        await message.answer("*❌ Iltimos, to‘g‘ri kanal ID’sini kiriting!*\n\nMasalan: *@example_channel* yoki *-1001234567890*", parse_mode="Markdown")
        await state.clear()
        return
    await state.update_data(channel_id=channel_id)
    await message.answer("*🌐 Kanal linkini kiriting:*\n\nMasalan: *https://t.me/example_channel*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_channel_link)

@dp.message(AdminStates.waiting_for_channel_link, lambda message: message.from_user.id in ADMINS)
async def handle_channel_link(message: Message, state: FSMContext):
    channel_link = message.text
    if not channel_link.startswith("https://t.me/"):
        await message.answer("*❌ Iltimos, to‘g‘ri kanal linkini kiriting!*\n\nMasalan: *https://t.me/example_channel*", parse_mode="Markdown")
        await state.clear()
        return
    user_data = await state.get_data()
    channel_name = user_data.get("channel_name")
    channel_id = user_data.get("channel_id")
    if not channel_name or not channel_id or not channel_link:
        await message.answer("*❌ Kanal nomi, ID yoki linki kiritilmagan!*\n\nQayta urinib ko‘ring.", parse_mode="Markdown")
        await state.clear()
        return
    await set_channel(message, bot, state, channel_name, channel_id, channel_link)
    global CHANNEL_ID
    CHANNEL_ID = channel_id
    await message.answer(f"*🌐 Kanal muvaffaqiyatli qo'shildi! Nom: {channel_name} | ID: {channel_id} | Link: {channel_link}*\n\nKanalni tekshirib ko‘ring!", parse_mode="Markdown")
    await state.clear()

@dp.message(AdminStates.waiting_for_movie_link, lambda message: message.from_user.id in ADMINS)
async def handle_movie_link(message: Message, state: FSMContext):
    movie_link = message.text
    if not movie_link.startswith("https://t.me/"):
        await message.answer("*❌ Iltimos, to‘g‘ri kino manzilini (link) kiriting!*\n\nMasalan: *https://t.me/example_channel/123*", parse_mode="Markdown")
        return
    await state.update_data(movie_link=movie_link)
    await message.answer("*📎 Kino nomini kiriting:*\n\nMasalan: *Qahramonlar Filmi*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_movie_name)

@dp.message(AdminStates.waiting_for_movie_name, lambda message: message.from_user.id in ADMINS)
async def handle_movie_name(message: Message, state: FSMContext):
    movie_name = message.text
    user_data = await state.get_data()
    movie_link = user_data.get("movie_link")
    if not movie_name or not movie_link:
        await message.answer("*❌ Kino nomi yoki manzili kiritilmagan!*\n\nQayta urinib ko‘ring.", parse_mode="Markdown")
        await state.clear()
        return
    await add_movie(message, bot, state, movie_name, movie_link)
    await message.answer(f"*🎬 Kino muvaffaqiyatli qo'shildi! Nom: {movie_name} | Link: {movie_link}*\n\nRahmat, yangi kino uchun! 🎥", parse_mode="Markdown")
    await state.clear()

@dp.message(AdminStates.waiting_for_movie_id, lambda message: message.from_user.id in ADMINS)
async def handle_movie_id_for_edit(message: Message, state: FSMContext):
    movie_id = message.text
    if not movie_id.isdigit():
        await message.answer("*❌ Iltimos, to‘g‘ri kino ID’sini kiriting!*\n\nMasalan: *1*", parse_mode="Markdown")
        await state.clear()
        return
    await state.update_data(movie_id=movie_id)
    await message.answer("*✏️ Yangi nom yoki linkni kiriting:*\n\nMasalan: *Yangi Kino* yoki *https://t.me/example_channel/123*", parse_mode="Markdown")
    await state.set_state(AdminStates.waiting_for_movie_new_value)

@dp.message(AdminStates.waiting_for_movie_new_value, lambda message: message.from_user.id in ADMINS)
async def handle_movie_new_value(message: Message, state: FSMContext):
    new_value = message.text
    user_data = await state.get_data()
    movie_id = user_data.get("movie_id")
    if not movie_id or not new_value:
        await message.answer("*❌ Kino ID yoki yangi qiymat kiritilmagan!*\n\nQayta urinib ko‘ring.", parse_mode="Markdown")
        await state.clear()
        return
    await edit_movie(message, bot, state, movie_id, new_value)
    await message.answer(f"*✏️ Kino (ID: {movie_id}) muvaffaqiyatli tahrirlandi!*\n\nYangi qiymat: *{new_value}*", parse_mode="Markdown")
    await state.clear()

@dp.message(AdminStates.waiting_for_delete_movie, lambda message: message.from_user.id in ADMINS)
async def handle_delete_movie(message: Message, state: FSMContext):
    movie_id = message.text
    if not movie_id.isdigit():
        await message.answer("*❌ Iltimos, to‘g‘ri kino ID’sini kiriting!*\n\nMasalan: *1*", parse_mode="Markdown")
        await state.clear()
        return
    await delete_movie(message, bot, state, movie_id)
    await message.answer(f"*🗑️ Kino (ID: {movie_id}) muvaffaqiyatli o'chirildi!*\n\nRahmat, buni uchun!", parse_mode="Markdown")
    await state.clear()

@dp.message(AdminStates.waiting_for_delete_channel, lambda message: message.from_user.id in ADMINS)
async def handle_delete_channel(message: Message, state: FSMContext):
    channel_id = message.text
    if not (channel_id.startswith('@') or channel_id.startswith('-100')):
        await message.answer("*❌ Iltimos, to‘g‘ri kanal ID’sini kiriting!*\n\nMasalan: *@example_channel* yoki *-1001234567890*", parse_mode="Markdown")
        await state.clear()
        return
    await delete_channel(message, bot, state, channel_id)
    global CHANNEL_ID
    if CHANNEL_ID == channel_id:
        CHANNEL_ID = "@DefaultChannel"
        await message.answer(f"*🗑️ Kanal {channel_id} muvaffaqiyatli o'chirildi!*\n\nStandart kanalga qaytdik: @DefaultChannel*", parse_mode="Markdown")
    else:
        await message.answer("*❌ Bunday kanal topilmadi!*\n\nKanal ID’sini qayta tekshirib ko‘ring.", parse_mode="Markdown")
    await state.clear()

@dp.message(AdminStates.waiting_for_edit_channel, lambda message: message.from_user.id in ADMINS)
async def handle_edit_channel(message: Message, state: FSMContext):
    args = message.text.split()
    if len(args) < 2:
        await message.answer("*❌ Iltimos, <eski_ID> <yangi_ID> kiriting!*\n\nMasalan: *@old_channel @new_channel*", parse_mode="Markdown")
        await state.clear()
        return
    old_channel_id, new_channel_id = args[0], args[1]
    if not (old_channel_id.startswith('@') or old_channel_id.startswith('-100')) or not (new_channel_id.startswith('@') or new_channel_id.startswith('-100')):
        await message.answer("*❌ Iltimos, to‘g‘ri kanal ID’larini kiriting!*\n\nMasalan: *@old_channel @new_channel*", parse_mode="Markdown")
        await state.clear()
        return
    await edit_channel(message, bot, state, old_channel_id, new_channel_id)
    global CHANNEL_ID
    if CHANNEL_ID == old_channel_id:
        CHANNEL_ID = new_channel_id
        await message.answer(f"*✏️ Kanal {old_channel_id} yangi ID {new_channel_id} bilan muvaffaqiyatli tahrirlandi!*\n\nKanalni tekshirib ko‘ring!", parse_mode="Markdown")
    else:
        await message.answer("*❌ Bunday kanal topilmadi!*\n\nEski kanal ID’sini qayta tekshirib ko‘ring.", parse_mode="Markdown")
    await state.clear()

# Foydalanuvchi va admin uchun kino ID’si handler’i
@dp.message(UserStates.waiting_for_movie_id, lambda message: True)  # Har bir foydalanuvchi uchun, admin ham
async def handle_movie_id(message: Message, state: FSMContext):
    movie_id = message.text
    if not movie_id.isdigit():
        await message.answer("*❌ Iltimos, to‘g‘ri kino ID’sini kiriting!*\n\nMasalan: *1*", parse_mode="Markdown")
        return
    await send_movie(message, bot, state, movie_id)
    await state.clear()

# Handler'lar
dp.message.register(request_movie, Command(commands=["get_movie"]))
dp.message.register(add_movie, Command(commands=["add_movie"]))
dp.message.register(edit_movie, Command(commands=["edit_movie"]))
dp.message.register(delete_movie, Command(commands=["delete_movie"]))
dp.message.register(set_channel, Command(commands=["set_channel"]))

if __name__ == "__main__":
<<<<<<< HEAD
    dp.run_polling(bot)
=======
    asyncio.run(main())
>>>>>>> debfd7ef3f458ec647871567d00ee63d1ed25fbc
