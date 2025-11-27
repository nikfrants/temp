# main.py
import asyncio
import logging
import os


from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from dotenv import load_dotenv

# !!! ИМПОРТИРУЕМ ВСЕ РОУТЕРЫ !!!
from bot_logic.registration.handlers import router as registration_router
from bot_logic.transfer.handlers import router as transfer_router
from bot_logic.common.handlers import router as common_router


async def main():
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        logging.error("Ошибка: не найден токен бота. Проверьте ваш .env файл.")
        return

    bot = Bot(token=bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher()

    # !!! ПОДКЛЮЧАЕМ ВСЕ РОУТЕРЫ !!!
    # Важно: Порядок регистрации роутеров имеет значение.
    # Более специфичные роутеры (например, регистрация, трансфер)
    # должны быть зарегистрированы раньше более общих (common),
    # чтобы их хэндлеры срабатывали первыми.
    dp.include_router(registration_router)
    dp.include_router(transfer_router)
    dp.include_router(common_router)


    # --- Регистрация команд бота для "синего меню" ---
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        # BotCommand(command="cancel", description="Отменить всё и вернуться в главное меню"),
    ]
    await bot.set_my_commands(commands)
    logging.info("Команды бота успешно установлены.")


    await bot.delete_webhook(drop_pending_updates=True)

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен.")

