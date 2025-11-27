# database/db_stubs.py
import random
import logging
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from oldbot.database.clients_excel_db import ClientsExcelManager # Импортируем наш новый класс

logger = logging.getLogger(__name__)
clients_db = ClientsExcelManager(file_path='database/data/clients.xlsx')

# Define file paths for persistence
_DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
_APPLICATIONS_DIR = os.path.join(_DATA_DIR, 'applications')

# Ensure the data directory and applications directory exist
os.makedirs(_DATA_DIR, exist_ok=True)
os.makedirs(_APPLICATIONS_DIR, exist_ok=True)

# ====================
# ФАСАД ДЛЯ КЛИЕНТОВ
# ====================

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """
    Проверяет, есть ли пользователь в базе.
    Возвращает данные пользователя или None.

    Эта функция теперь является фасадом для ClientsExcelManager.
    """
    logger.info(f"Проверка пользователя {user_id} в БД (через Excel-файл).")
    # Перенаправляем вызов к новому классу
    return clients_db.get_user(user_id)


async def create_or_update_user(user_id: int, user_profile_data: dict) -> bool:
    """
    Создает нового пользователя или обновляет существующего в БД.
    user_profile_data должен содержать только данные профиля пользователя.

    Эта функция теперь является фасадом для ClientsExcelManager.
    """
    logger.info(f"Создание/обновление пользователя ID:{user_id} в БД (через Excel-файл).")
    # Перенаправляем вызов к новому классу
    return clients_db.create_or_update_user(user_id, user_profile_data)


# ====================
# ФАСАД ДЛЯ ЗАЯВОК
# ====================

async def create_application(user_id: int, data: dict):
    """
    Сохраняет новую заявку в отдельный JSON-файл.
    Возвращает номер созданной заявки.
    """
    # Генерируем уникальный ID на основе timestamp и случайного числа
    app_id = int(datetime.now().timestamp() * 1000) + random.randint(1, 1000)

    application_data = {
        "id": app_id,
        "user_id": user_id,
        "timestamp": datetime.now().isoformat(),
        "selected_event_id": data.get('selected_event_id'),
        "event_id": data.get('event_id'),
        "event_name": data.get('event_name'),
        "current_option_type": data.get('current_option_type'),
        "selected_point_index": data.get('selected_point_index'),
        "date": data.get('selected_point_name'),
        "selected_date": data.get('selected_date'),
        "selected_time": data.get('selected_time'),
        "pre_repair": data.get('pre_repair'),
        "pre_repair_comment": data.get('pre_repair_comment'),
    }

    file_path = os.path.join(_APPLICATIONS_DIR, f"app_{app_id}.json")
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(application_data, f, ensure_ascii=False, indent=4)
        logger.info(f"Создана заявка #{app_id} для пользователя {user_id} в файле {file_path}")
        return app_id
    except Exception as e:
        logger.error(f"Ошибка при сохранении заявки #{app_id} в файл {file_path}: {e}")
        return None

async def get_application_by_id(app_id: int):
    """
    Возвращает данные заявки из соответствующего файла.
    """
    file_path = os.path.join(_APPLICATIONS_DIR, f"app_{app_id}.json")
    if not os.path.exists(file_path):
        logger.warning(f"Файл заявки {file_path} не найден.")
        return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка при чтении файла заявки {file_path}: {e}")
        return None

async def delete_application(app_id: int):
    """
    Удаляет файл заявки по ID.
    """
    file_path = os.path.join(_APPLICATIONS_DIR, f"app_{app_id}.json")
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            logger.info(f"Файл заявки {file_path} успешно удален.")
            return True
        except OSError as e:
            logger.error(f"Ошибка при удалении файла заявки {file_path}: {e}")
            return False
    else:
        logger.warning(f"Файл заявки {file_path} не найден для удаления.")
        return False

