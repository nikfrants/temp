import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage  # Пока Memory, потом Redis подключим

# Импорты наших модулей
import config
from database.excel_impl import ExcelRepository

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Инициализация бота...")

    # 1. Инициализация Базы Данных
    # Бот создает экземпляр репозитория один раз и передает его в хендлеры
    repo = ExcelRepository(config.EXCEL_DB_PATH)

    # 2. Бот и Диспетчер
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Внедрение зависимостей (Dependency Injection)
    # Это крутая штука: теперь в любом хендлере можно получить `repo`
    dp["repo"] = repo

    # 4. Регистрация роутеров (создадим их на следующем шаге)
    # from bot_logic.handlers import common, registration, transfer
    # dp.include_router(common.router)
    # dp.include_router(registration.router)

    logger.info("Бот запущен!")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")
