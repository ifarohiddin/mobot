import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

# Configuration
API_TOKEN = "7202873256:AAEK_kjOD6P3kF4pM5ZqUehff0u5DAQzpfo"
CHANNEL_ID = "-1001927486162"  # Replace with your channel ID
CHANNEL_URL = "https://t.me/i_farohiddin"

# Filmlar ro'yxati - endi har bir kino uchun nomi ham saqlayapti
MOVIE_STORAGE = {
    "1": {"url": "https://t.me/mykino_server/2", "name": "Sehrli Qirollik"},
    "2": {"url": "https://t.me/mykino_server/3", "name": "Medellin"},
    "3": {"url": "https://t.me/mykino_server/4", "name": "Qutqaruv operatsiyasi"}
}

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def check_subscription(user_id: int) -> bool:
    """Check if user is subscribed to the channel."""
    try:
        member = await bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"Error checking subscription: {e}")
        return False

def get_subscription_keyboard() -> InlineKeyboardMarkup:
    """Create keyboard with subscription button."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➡️ Kanalga o'tish",
                    url=CHANNEL_URL
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅ Obunani tekshirish",
                    callback_data="check_subs"
                )
            ]
        ]
    )

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    """Handle /start command."""
    try:
        user_id = message.from_user.id
        is_subscribed = await check_subscription(user_id)
        
        if not is_subscribed:
            keyboard = get_subscription_keyboard()
            await message.answer(
                "⛔ Botdan foydalanish uchun kanalimizga a'zo bo'ling:",
                reply_markup=keyboard
            )
        else:
            await message.answer(
                "✅ Xush kelibsiz! Iltimos, kino kodini yuboring:"
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
            await call.answer("⛔ Siz hali kanalga a'zo bo'lmagansiz!", show_alert=True)
        else:
            await call.message.edit_text(
                "✅ Obuna tasdiqlandi!\n\nIltimos, kino kodini yuboring:"
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
            await message.answer(
                "⛔ Botdan foydalanish uchun kanalimizga a'zo bo'ling:",
                reply_markup=keyboard
            )
            return

        movie_code = message.text.strip()
        
        if movie_code in MOVIE_STORAGE:
            try:
                # Kino yuklanmoqda xabarini yuborish
                await message.answer("🎬 Sizning kinongiz yuklanmoqda...")
                
                # Kino videofileni va pastida kino kodi va nomini yuborish
                movie_info = MOVIE_STORAGE[movie_code]
                await message.answer_video(
                    video=movie_info["url"],
                    caption=f"Kino kodi: {movie_code}\nNomi: {movie_info['name']}"
                )
            except TelegramBadRequest as e:
                logger.error(f"Error sending movie: {e}")
                await message.answer("❌ Kino yuborishda xatolik yuz berdi.")
        else:
            await message.answer(
                "❌ Noto'g'ri kino kodi kiritildi! Iltimos, to'g'ri kino kodini kiriting."
            )
    except Exception as e:
        logger.error(f"Error in movie handler: {e}")
        await message.answer("Xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.")

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