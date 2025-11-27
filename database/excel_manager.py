import xlwings as xw
import os
import sys
import json
import logging
import time
import shutil

# Настройка логирования для вывода в консоль
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)


class ExcelManager:
    """Класс для управления Excel-файлами с использованием xlwings."""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.app = None
        self.workbook = None

        # Проверка, не заблокирован ли файл
        if not self._is_file_locked():
            self.workbook = self._load_workbook()
        else:
            logging.error(
                f"Файл '{self.file_path}' открыт или заблокирован другим приложением. Пожалуйста, закройте его и попробуйте снова.")

    def _is_file_locked(self) -> bool:
        """Проверяет, заблокирован ли файл."""
        if not os.path.exists(self.file_path):
            return False

        try:
            os.rename(self.file_path, self.file_path)
            return False
        except OSError:
            return True

    def _col_to_letter(self, col_num: int) -> str:
        """Внутренняя утилита для конвертации номера столбца в букву (1 -> A, 27 -> AA)."""
        letter = ''
        while col_num > 0:
            col_num, remainder = divmod(col_num - 1, 26)
            letter = chr(65 + remainder) + letter
        return letter

    def _load_workbook(self):
        """Загружает или создает рабочую книгу, запуская Excel."""
        try:
            self.app = xw.App(visible=False, add_book=False)
            self.app.display_alerts = False
            self.app.screen_updating = False

            if os.path.exists(self.file_path):
                workbook = self.app.books.open(self.file_path)
                logging.debug(f"Успешно открыт файл: {self.file_path}")
            else:
                workbook = self.app.books.add()
                logging.info(f"Файл не найден по пути: {self.file_path}. Создана новая книга.")

            return workbook

        except Exception as e:
            logging.error(f"Ошибка при запуске Excel или загрузке файла {self.file_path}: {e}")
            self.close()
            return None

    def save(self):
        """
        Сохраняет рабочую книгу.
        Возвращает True в случае успеха, False в случае ошибки.
        """
        if self.workbook:
            try:
                self.workbook.save(self.file_path)
                logging.info(f"Файл '{self.file_path}' успешно сохранен.")
                return True
            except Exception as e:
                logging.error(f"Ошибка при сохранении файла {self.file_path}: {e}")
                return False
        return False

    def close(self):
        """Корректно закрывает книгу и выходит из приложения Excel."""
        if self.workbook:
            try:
                self.workbook.close()
            except Exception as e:
                logging.error(f"Ошибка при закрытии книги: {e}")
        if self.app:
            try:
                self.app.quit()
            except Exception as e:
                logging.error(f"Ошибка при выходе из приложения Excel: {e}")
        logging.info("Экземпляр Excel закрыт.")

    def get_sheet(self, sheet_name: str, create_if_not_exists: bool = False):
        """
        Возвращает лист по имени. Может создать его, если не существует.
        """
        if not self.workbook:
            return None

        for sheet in self.workbook.sheets:
            if sheet.name == sheet_name:
                return sheet

        if create_if_not_exists:
            logging.info(f"Лист '{sheet_name}' не найден, создаем новый.")
            try:
                new_sheet = self.workbook.sheets.add(sheet_name)
                return new_sheet
            except Exception as e:
                logging.error(f"Не удалось создать новый лист '{sheet_name}': {e}")
                return None
        else:
            return None

    def copy_and_rename_sheet(self, source_sheet_name: str, new_sheet_name: str):
        """Копирует существующий лист и переименовывает его."""
        if not self.workbook or source_sheet_name not in [s.name for s in self.workbook.sheets]:
            logging.error(f"Ошибка: Исходный лист '{source_sheet_name}' не найден.")
            return False

        source_sheet = self.workbook.sheets[source_sheet_name]
        source_sheet.copy(name=new_sheet_name)
        return True

    def find_cell(self, sheet_name: str, search_value):
        """Ищет ячейку по значению и возвращает её координаты (столбец-буква, строка-номер)."""
        sheet = self.get_sheet(sheet_name)
        if not sheet:
            logging.error(f"Ошибка: Лист '{sheet_name}' не найден.")
            return None

        data = sheet.used_range.value
        if not data:
            return None

        for r_idx, row in enumerate(data):
            for c_idx, cell_value in enumerate(row):
                if cell_value == search_value:
                    col_letter = self._col_to_letter(c_idx + 1)
                    row_num = r_idx + 1
                    return col_letter, row_num

        logging.info(f"Значение '{search_value}' не найдено на листе '{sheet_name}'.")
        return None

    def delete_sheet(self, sheet_name: str):
        """Удаляет лист."""
        if not self.workbook or sheet_name not in [s.name for s in self.workbook.sheets]:
            logging.error(f"Ошибка: Лист '{sheet_name}' не найден.")
            return False

        self.workbook.sheets[sheet_name].delete()
        return True

    def read_sheet_to_dict(self, sheet_name: str, key_column: str = 'A'):
        """
        Читает данные из листа и возвращает их в виде словаря.
        Пропускает первую строку (заголовки).
        """
        sheet = self.get_sheet(sheet_name)
        if not sheet:
            logging.error(f"Ошибка: Лист '{sheet_name}' не найден.")
            return None

        key_col_index = ord(key_column.upper()) - ord('A')
        data = {}
        all_values = sheet.used_range.value

        if not all_values or not isinstance(all_values, list) or len(all_values) < 2:
            return data

        for row in all_values[1:]:
            if isinstance(row, list) and len(row) > key_col_index:
                key = row[key_col_index]
                if key:
                    data[key] = tuple(row)

        return data


# ---
# Код для работы с логикой проекта

TEMPLATE_STRUCTURE_SHEET_NAME = "Структура шаблона"
TEMPLATE_SHEET_NAME = "Шаблон события"
EVENTS_SHEET_NAME = "Текущие события"
PID_FILE = 'excel_manager.pid'
# APPLICATIONS_DIR = os.path.join('C:/Users/Nikolay/PycharmProjects/transfer_tg_bot/database/data/applications')
APPLICATIONS_DIR = os.path.join('D:/sync/2 way BikeFit Lab - nikolay mac/transfer/transfer_tg_bot/database/data/applications')
PROCESSED_APPLICATIONS_DIR = os.path.join(APPLICATIONS_DIR, 'applications_done')


def setup_base_sheets(manager: ExcelManager):
    """Настраивает базовые листы."""
    logging.info("Настройка базовых листов...")
    template_struct_sheet = manager.get_sheet(TEMPLATE_STRUCTURE_SHEET_NAME, create_if_not_exists=True)
    if template_struct_sheet and template_struct_sheet.used_range.last_cell.row <= 1:
        template_struct_sheet.range('A1').value = ['Номер столбца', 'Кодовое название', 'Название (рус)']
        structure_data = [
            (1, 'appNumber', 'номер заявки'), (2, 'fullName', 'фио'), (3, 'phone', 'телефон'),
            (4, 'email', 'почта'), (5, 'telegramID', 'телеграм id'), (6, 'pasportNumber', 'паспорт номер'),
            (7, 'pasportAddress', 'паспорт адрес'), (8, 'pasportDate', 'паспорт дата'),
            (9, 'appDate', 'дата заявки'), (10, 'deliveryDate', 'дата сдачи'),
            (11, 'pickupDate', 'дата забора'), (12, 'deliveryPlace', 'место сдачи'),
            (13, 'pickupPlace', 'место забора'), (14, 'maintenanceNeeded', 'надо ТО'),
            (15, 'comment', 'комментарии'), (16, 'generalComment', 'общий комментарий'),
        ]
        template_struct_sheet.range('A2').value = structure_data
        logging.info("Лист 'Структура шаблона' инициализирован.")

    events_sheet = manager.get_sheet(EVENTS_SHEET_NAME, create_if_not_exists=True)
    if not events_sheet:
        logging.error(f"Ошибка: лист '{EVENTS_SHEET_NAME}' не найден и не может быть создан.")
    else:
        logging.info(f"Лист '{EVENTS_SHEET_NAME}' найден. Инициализация не требуется.")


def create_event_sheet(manager: ExcelManager, event_name: str, template_structure: dict):
    """Создает новый лист для события, копируя шаблон и заполняя его заголовками."""
    if manager.copy_and_rename_sheet(TEMPLATE_SHEET_NAME, event_name):
        event_sheet = manager.get_sheet(event_name)
        if event_sheet:
            for col_num, row_data in template_structure.items():
                col_name_ru = row_data[2]
                event_sheet.range(1, int(col_num)).value = col_name_ru
            return True
    return False


def init_excel_project(manager: ExcelManager, template_structure: dict):
    """
    Режим инициализации.
    Создает листы для событий из 'Текущие события'.
    """
    logging.info("Запуск инициализации проекта...")

    if 'Текущие события' not in [s.name for s in manager.workbook.sheets]:
        logging.error("Ошибка: Лист 'Текущие события' не найден. Невозможно инициализировать проект.")
        return False

    events_sheet = manager.workbook.sheets['Текущие события']
    last_col = events_sheet.range('A1').expand('right').last_cell.column

    for col_index in range(2, last_col + 1):
        event_name = events_sheet.range(1, col_index).value
        event_year_value = events_sheet.range(3, col_index).value

        if not event_name or not event_year_value:
            continue

        try:
            event_year = int(event_year_value)
        except (ValueError, TypeError):
            logging.warning(
                f"Не удалось преобразовать год '{event_year_value}' в число для события '{event_name}'. Пропускаем.")
            continue

        sheet_title = f"{event_name} {event_year}"

        if sheet_title in [s.name for s in manager.workbook.sheets]:
            logging.info(f"Лист для события '{sheet_title}' уже существует. Пропускаем.")
        else:
            logging.info(f"Создаем новый лист для события: '{sheet_title}'...")
            if not create_event_sheet(manager, sheet_title, template_structure):
                logging.error(f"Не удалось создать и заполнить лист '{sheet_title}'.")

    logging.info("Инициализация проекта завершена.")
    return True


def process_new_delivery_request(manager: ExcelManager, request_data: dict, template_structure: dict):
    """Обрабатывает новую заявку, записывая её в нужный лист."""
    event_name = request_data.get('event_name')
    if not event_name:
        logging.error("Ошибка: В данных заявки отсутствует 'event_name'.")
        return False

    event_sheet = manager.get_sheet(event_name)
    if not event_sheet:
        logging.error(f"Ошибка: Лист '{event_name}' не найден. Заявка не может быть обработана.")
        return False

    next_row = event_sheet.used_range.last_cell.row + 1

    for col_num, row_data in template_structure.items():
        key_name = row_data[1]
        value = request_data.get(key_name)
        if value is not None:
            event_sheet.range(next_row, int(col_num)).value = value

    logging.info(f"Новая заявка успешно добавлена на лист '{event_name}'.")
    return True


def is_another_instance_running():
    """Проверяет, запущен ли уже другой экземпляр этого скрипта."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE, 'r') as f:
                pid = int(f.read().strip())
            try:
                os.kill(pid, 0)
                logging.info(f"Другой экземпляр с PID {pid} уже запущен.")
                return True
            except OSError:
                logging.warning(f"Найден устаревший PID-файл ({PID_FILE}). Удаляем.")
                os.remove(PID_FILE)
                return False
        except (ValueError, FileNotFoundError):
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
            return False
    return False


def create_pid_file():
    """Создает PID-файл с PID текущего процесса."""
    try:
        with open(PID_FILE, 'w') as f:
            f.write(str(os.getpid()))
    except Exception as e:
        logging.error(f"Не удалось создать PID-файл: {e}")
        sys.exit(1)


def main():
    """Основная функция-обработчик."""
    if is_another_instance_running():
        sys.exit(0)

    create_pid_file()

    manager = None
    try:
        if not os.path.exists(APPLICATIONS_DIR):
            os.makedirs(APPLICATIONS_DIR, exist_ok=True)
            logging.info(f"Создана директория для заявок: {APPLICATIONS_DIR}")

        if not os.path.exists(PROCESSED_APPLICATIONS_DIR):
            os.makedirs(PROCESSED_APPLICATIONS_DIR, exist_ok=True)
            logging.info(f"Создана директория для обработанных заявок: {PROCESSED_APPLICATIONS_DIR}")

        # excel_file = 'C:/Users/Nikolay/PycharmProjects/transfer_tg_bot/database/data/applications.xlsm'
        excel_file = 'D:/sync/2 way BikeFit Lab - nikolay mac/transfer/transfer_tg_bot/database/data/applications.xlsm'
        manager = ExcelManager(excel_file)

        if not manager.workbook:
            logging.error("Не удалось загрузить рабочую книгу Excel. Завершение работы.")
            sys.exit(1)

        setup_base_sheets(manager)

        template_structure_data = manager.read_sheet_to_dict(TEMPLATE_STRUCTURE_SHEET_NAME, key_column='A')
        if not template_structure_data:
            logging.error("Не удалось считать структуру шаблона. Заявки не будут обработаны.")
            manager.save()
            sys.exit(1)

        init_excel_project(manager, template_structure_data)

        json_files = [f for f in os.listdir(APPLICATIONS_DIR) if f.endswith('.json')]
        if not json_files:
            logging.info("Нет новых заявок для обработки.")
        else:
            for json_file_name in json_files:
                json_file_path = os.path.join(APPLICATIONS_DIR, json_file_name)
                logging.info(f"Найдена новая заявка: {json_file_name}. Начинаем обработку.")
                try:
                    with open(json_file_path, 'r', encoding='utf-8') as f:
                        request_data = json.load(f)

                    if process_new_delivery_request(manager, request_data, template_structure_data):
                        processed_file_path = os.path.join(PROCESSED_APPLICATIONS_DIR, json_file_name)
                        shutil.move(json_file_path, processed_file_path)
                        logging.info(
                            f"Заявка {json_file_name} успешно обработана и перемещена в '{PROCESSED_APPLICATIONS_DIR}'.")
                    else:
                        logging.error(f"Не удалось обработать заявку {json_file_name}.")
                except (json.JSONDecodeError, FileNotFoundError, shutil.Error) as e:
                    logging.error(
                        f"Ошибка при чтении или перемещении файла {json_file_name}: {e}. Файл будет переименован.")
                    os.rename(json_file_path, json_file_path + ".error")

        manager.save()

    finally:
        if manager:
            manager.close()
        if os.path.exists(PID_FILE):
            os.remove(PID_FILE)
            logging.info("PID-файл удален. Процесс завершен.")


if __name__ == "__main__":
    main()
