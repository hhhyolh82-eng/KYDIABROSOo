"""
Основной модуль Telegram-бота на aiogram 3.x.
Регистрирует хэндлеры команд и callback-ов,
а также предоставляет функцию для отправки фото пользователю.
"""

import os
import base64
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BufferedInputFile
)
from aiogram.filters import Command
from aiogram.enums import ParseMode

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEB_APP_URL = os.getenv("WEB_APP_URL", "https://localhost:8000")
USE_WEBHOOK = os.getenv("USE_WEBHOOK", "false").lower() == "true"

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()


def get_main_keyboard() -> InlineKeyboardMarkup:
    """Возвращает основную клавиатуру с инлайн-кнопками."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📸 Сделать фото",
                    callback_data="take_photo"
                ),
                InlineKeyboardButton(
                    text="🔗 Получить ссылку",
                    callback_data="get_link"
                ),
            ]
        ]
    )


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start."""
    await message.answer(
        "👋 Привет! Я бот для работы с камерой.\n\n"
        "Выбери нужное действие:",
        reply_markup=get_main_keyboard()
    )


@dp.callback_query(F.data == "take_photo")
async def process_take_photo(callback: types.CallbackQuery):
    """
    Обработчик кнопки 'Сделать фото'.
    Пока что информирует пользователя о том, что нужно использовать ссылку.
    """
    await callback.answer(
        "📸 Используй кнопку 'Получить ссылку' для доступа к камере через браузер.",
        show_alert=True
    )


@dp.callback_query(F.data == "get_link")
async def process_get_link(callback: types.CallbackQuery):
    """Генерирует уникальную ссылку для пользователя."""
    user_id = callback.from_user.id
    unique_link = f"{WEB_APP_URL}/photo/{user_id}"

    await callback.message.answer(
        f"🔗 <b>Перейдите по ссылке и разрешите доступ к камере:</b>\n\n"
        f"<a href='{unique_link}'>{unique_link}</a>\n\n"
        f"⚠️ Убедитесь, что открываете ссылку в браузере (Safari/Chrome), "
        f"а не внутри Telegram, если камера не запрашивается.",
        disable_web_page_preview=True
    )
    await callback.answer()


async def send_photos_to_user(
    user_id: int,
    front_photo_b64: str,
    back_photo_b64: str
) -> None:
    """
    Отправляет два фото пользователю в Telegram.
    Вызывается из web_app.py при получении данных с веб-страницы.
    """
    try:
        # Декодируем base64 в байты
        front_data = base64.b64decode(front_photo_b64)
        back_data = base64.b64decode(back_photo_b64)

        # Отправляем фото с фронтальной камеры
        await bot.send_photo(
            chat_id=user_id,
            photo=BufferedInputFile(front_data, filename="front.jpg"),
            caption="📱 <b>Фронтальная камера</b>"
        )

        # Отправляем фото с основной камеры
        await bot.send_photo(
            chat_id=user_id,
            photo=BufferedInputFile(back_data, filename="back.jpg"),
            caption="📷 <b>Основная камера</b>"
        )

    except Exception as e:
        print(f"[ERROR] Ошибка при отправке фото: {e}")
        await bot.send_message(
            chat_id=user_id,
            text="❌ Не удалось обработать или отправить фото. "
                 "Попробуйте ещё раз."
        )


async def on_startup() -> None:
    """Настройка вебхука или его удаление при использовании polling."""
    if USE_WEBHOOK:
        webhook_url = f"{WEB_APP_URL}/webhook/bot"
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
        print(f"[INFO] Вебхук установлен: {webhook_url}")
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        print("[INFO] Вебхук удалён, используется polling.")


async def start_polling() -> None:
    """Запускает бота в режиме long-polling."""
    await on_startup()
    await dp.start_polling(bot)


# Точка входа для отдельного запуска бота (без веб-сервера)
if __name__ == "__main__":
    asyncio.run(start_polling())
