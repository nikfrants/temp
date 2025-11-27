import asyncio
import logging
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from handlers import router

async def main():
    """
    Основная функция для запуска бота.
    """
    # Настройка логирования для отладки
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    )
    try:
        with open("token", "r") as f:
            bot_token = f.read().strip()
    except FileNotFoundError:
        logging.error("Файл 'token' не найден. Убедитесь, что он лежит рядом со скриптом.")
        bot_token = None

    if not bot_token:
        logging.error("Токен бота не найден. Убедитесь, что он задан в файле 'token'.")
        # Добавь здесь свою логику, что делать, если токен не найден
        # Например, exit() или raise Exception
    # # Загрузка переменных окружения из файла .env
    # load_dotenv()
    # bot_token = os.getenv("BOT_TOKEN")
    # if not bot_token:
    #     logging.error("Токен бота не найден. Убедитесь, что он задан в файле .env")
    #     return

    # Инициализация бота и диспетчера
    # MemoryStorage будет хранить состояния FSM в оперативной памяти
    storage = MemoryStorage()
    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=storage)

    # Подключаем роутер с нашими обработчиками
    dp.include_router(router)

    # Удаляем вебхук и запускаем polling
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        logging.info("Бот запускается...")
        await dp.start_polling(bot)
    finally:
        await bot.session.close()




if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен.")