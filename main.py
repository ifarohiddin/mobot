import logging
import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

# Configuration
API_TOKEN = "7876488844:AAFLtipD2pfKgfESPj1PSCWaF9NAqnzImZM"
MOVIES_FILE = "movies.json"  # Kinolarni saqlash uchun fayl nomi
CHANNELS_FILE = "channels.json"  # Kanallar ma'lumotlarini saqlash uchun fayl

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

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

# Bot ishga tushganda kinolarni va kanallarni yuklash
MOVIE_STORAGE = load_movies()
CHANNELS = load_channels()

async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed to all required channels."""
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

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """Handle /start command."""
    try:
        user_id = message.from_user.id
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
                f"✅ Xush kelibsiz! Quyidagi kino kodlaridan birini yuboring:\n\n{movie_list}"
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
                f"✅ Obuna tasdiqlandi!\n\nQuyidagi kino kodlaridan birini yuboring:\n{movie_list}"
            )
    except Exception as e:
        logger.error(f"Error in subscription check: {e}")
        await call.answer("Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.", show_alert=True)

@dp.message()
async def send_movie(message: types.Message):
    """Handle movie requests."""
    try:
        is_subscribed = await check_subscription(message.from_user.id)
        
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
        global MOVIE_STORAGE
        MOVIE_STORAGE = load_movies()

        if movie_code in MOVIE_STORAGE:
            movie_info = MOVIE_STORAGE[movie_code]
            await message.answer_video(
                video=movie_info["url"],
                caption=f"Kino kodi: {movie_code}\nNomi: {movie_info['name']}"
            )
        else:
            movie_list = "\n".join([f"{code} - {info['name']}" for code, info in MOVIE_STORAGE.items()])
            await message.answer(f"❌ Noto'g'ri kino kodi kiritildi!\n\nMavjud kino kodlari:\n{movie_list}")
    except Exception as e:
        logger.error(f"Error in movie handler: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

@dp.message(Command("add_movie"))
async def add_movie(message: types.Message):
    """Admin kinoni qo'shish uchun buyruq."""
    if message.from_user.id != ADMIN_ID:  # Faqat admin qo'sha oladi
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

        await message.answer(f"✅ Kino qo'shildi!\n\n🎬 {name} ({code})")
    except Exception as e:
        await message.answer("❌ Format noto'g'ri! Quyidagi ko'rinishda kiriting:\n\n`/add_movie 4|https://t.me/link|Yangi Kino`", parse_mode="Markdown")

@dp.message(Command("add_channel"))
async def add_channel(message: types.Message):
    """Admin kanal qo'shish uchun buyruq."""
    if message.from_user.id != ADMIN_ID:  # Faqat admin qo'sha oladi
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
        global CHANNELS
        CHANNELS = channels

        await message.answer(f"✅ Kanal qo'shildi!\n\n📢 {name} ({code})")
    except Exception as e:
        await message.answer("❌ Format noto'g'ri! Quyidagi ko'rinishda kiriting:\n\n`/add_channel kanal_kodi|-100123456789|https://t.me/kanal|Kanal Nomi`", parse_mode="Markdown")

@dp.message(Command("remove_channel"))
async def remove_channel(message: types.Message):
    """Admin kanalni o'chirish uchun buyruq."""
    if message.from_user.id != ADMIN_ID:  # Faqat admin o'chira oladi
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
            global CHANNELS
            CHANNELS = channels
            
            await message.answer(f"✅ Kanal o'chirildi!\n\n📢 {channel_name} ({channel_code})")
        else:
            await message.answer(f"❌ '{channel_code}' kodi bilan kanal topilmadi!")
    except Exception as e:
        await message.answer("❌ Format noto'g'ri! Quyidagi ko'rinishda kiriting:\n\n`/remove_channel kanal_kodi`", parse_mode="Markdown")

@dp.message(Command("list_channels"))
async def list_channels(message: types.Message):
    """Admin uchun mavjud kanallar ro'yxatini ko'rsatish."""
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ Sizda bu buyruqdan foydalanish huquqi yo'q!")
        return
    
    channels = load_channels()
    if not channels:
        await message.answer("ℹ️ Hozircha hech qanday kanal qo'shilmagan.")
        return
    
    channel_list = "\n\n".join([f"📢 {info['name']}\nKod: {code}\nID: {info['id']}\nURL: {info['url']}" 
                              for code, info in channels.items()])
    
    await message.answer(f"📋 Mavjud kanallar ro'yxati:\n\n{channel_list}")

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