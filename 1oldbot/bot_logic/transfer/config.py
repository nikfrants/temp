# bot_logic/transfer/config.py
import json
import os

# Получаем директорию текущего скрипта (config.py)
# Поскольку config.json находится в той же папке, что и config.py,
# этот путь будет корректным.
current_script_dir = os.path.dirname(os.path.abspath(__file__))
config_file_path = os.path.join(current_script_dir, 'config.json')

# Переменная, которая будет хранить загруженную конфигурацию
TRANSFER_CONFIG = {}

try:
    with open(config_file_path, 'r', encoding='utf-8') as f:
        TRANSFER_CONFIG = json.load(f)
    print(f"Конфигурация успешно загружена из: {config_file_path}") # Для отладки
except FileNotFoundError:
    print(f"ОШИБКА: Файл config.json не найден по пути: {config_file_path}. Убедитесь, что он существует.")
    # Установите пустую или дефолтную конфигурацию в случае ошибки
    TRANSFER_CONFIG = {"admin_ids": [], "events": []}
except json.JSONDecodeError:
    print(f"ОШИБКА: Неверный формат JSON в файле: {config_file_path}. Проверьте содержимое.")
    TRANSFER_CONFIG = {"admin_ids": [], "events": []}

# Теперь TRANSFER_CONFIG содержит данные из config.json и может быть импортирован другими модулями.