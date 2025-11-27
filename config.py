import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Путь к файлу Excel (база данных)
# Используем raw-строку (r"path") или слеши /, чтобы не было проблем на Windows/Mac
EXCEL_DB_PATH = os.getenv("EXCEL_DB_PATH", "database/data/clients.xlsx")

# Настройки Redis (если будем использовать)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))