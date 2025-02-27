from aiogram import Bot, types
from aiogram.types import Update, Message
from aiogram.fsm.context import FSMContext
from typing import Union
import psycopg2
from dotenv import load_dotenv
import os
from urllib.parse import urlparse

load_dotenv()

async def send_movie(update: Union[Update, Message], bot: Bot, state: FSMContext, movie_id: str):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        if isinstance(update, Message):
            await update.reply("*❌ Ma'lumotlar bazasi ulanishi topilmadi!*\n\nRailway’dagi DATABASE_URL’ni tekshirib ko‘ring.", parse_mode="Markdown")
        return

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

    cursor.execute("SELECT name, link FROM movies WHERE id = %s", (movie_id,))
    movie = cursor.fetchone()

    if movie:
        name, link = movie
        # Telegram’dan video faylini olish va yuborish (file_id sifatida)
        try:
            file_id = link  # Ma'lumotlar bazasidagi link faqat file_id sifatida saqlanadi
            if isinstance(update, Message):
                await bot.send_video(
                    chat_id=update.chat.id,
                    video=file_id,
                    caption=f"*🎥 Kino:* *{name}*\n\nKino bilan zavqlaning, rahmat! 🍿",
                    parse_mode="Markdown"
                )
            else:
                await bot.send_video(
                    chat_id=update.message.chat.id,
                    video=file_id,
                    caption=f"*🎥 Kino:* *{name}*\n\nKino bilan zavqlaning, rahmat! 🍿",
                    parse_mode="Markdown"
                )
        except Exception as e:
            if isinstance(update, Message):
                await update.reply("*❌ Video yuborishda xatolik yuz berdi!*\n\nLinkni tekshirib ko‘ring yoki admin bilan bog‘laning.", parse_mode="Markdown")
            else:
                await update.message.reply("*❌ Video yuborishda xatolik yuz berdi!*\n\nLinkni tekshirib ko‘ring yoki admin bilan bog‘laning.", parse_mode="Markdown")
    else:
        if isinstance(update, Message):
            await update.reply("*❌ Bunday ID bilan kino topilmadi!*\n\nKino ID’sini qayta tekshirib ko‘ring, masalan: *123*.", parse_mode="Markdown")
        else:
            await update.message.reply("*❌ Bunday ID bilan kino topilmadi!*\n\nKino ID’sini qayta tekshirib ko‘ring, masalan: *123*.", parse_mode="Markdown")

    conn.close()