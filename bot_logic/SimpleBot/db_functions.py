import json
import logging
import os
from datetime import datetime

# --- "Заглушка" для проверки пользователя в базе ---
async def check_user_in_db(user_id: int) -> bool:
    """
    Имитирует проверку пользователя в базе данных.
    В реальном проекте здесь будет запрос к вашей БД.

    Возвращает True, если пользователь есть, и False, если нет.
    """
    logging.info(f"Проверка пользователя {user_id} в 'базе данных'...")
    # Для теста: считаем, что пользователи с четным ID есть в базе, а с нечетным - нет.
    return user_id % 2 == 0


# --- Сохранение заявки в JSON ---
APPLICATIONS_DIR = "applications"

async def save_application_to_json(data: dict):
    """
    Сохраняет данные заявки в JSON-файл.
    """
    if not os.path.exists(APPLICATIONS_DIR):
        os.makedirs(APPLICATIONS_DIR)

    # Создаем уникальное имя файла
    user_id = data.get('user_id')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"app_{user_id}_{timestamp}.json"
    file_path = os.path.join("D:/sync/2 way BikeFit Lab - nikolay mac/transfer/transfer_tg_bot/database/data/applications", file_name)
    # file_path = os.path.join("C:/Users/Nikolay/PycharmProjects/transfer_tg_bot/database/data/applications", file_name)

    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logging.info(f"Заявка сохранена в файл: {file_path}")
    except Exception as e:
        logging.error(f"Ошибка при сохранении заявки в файл: {e}")
