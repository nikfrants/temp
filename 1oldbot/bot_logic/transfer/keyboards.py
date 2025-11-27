# bot_logic/transfer/keyboards.py

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from oldbot.bot_logic.utils.utils import _add_back_button # Убедитесь, что _add_back_button доступна
from .config import TRANSFER_CONFIG # Импортируем из локального config.py
from datetime import datetime # Для сортировки и форматирования дат
import logging # Добавим логирование

logger = logging.getLogger(__name__)

# --- Клавиатуры для флоу трансфера ---

def get_events_keyboard(selected_event_id: str = None) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для выбора события с галочкой и кнопками Назад/Далее.
    :param selected_event_id: ID выбранного события, чтобы поставить галочку.
    """
    builder = InlineKeyboardBuilder()
    if not TRANSFER_CONFIG or 'events' not in TRANSFER_CONFIG:
        logger.error("TRANSFER_CONFIG или ключ 'events' не найден в keyboards.py.")
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Нет доступных событий", callback_data="no_events")]])

    for event in TRANSFER_CONFIG['events']:
        button_text = f"✅ {event['name']}" if str(event.get('id')) == str(selected_event_id) else event['name']
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"select_event_{event['id']}"))

    # Изменение порядка кнопок "Далее" и "Назад"
    builder.row(
        InlineKeyboardButton(text="Далее ➡️", callback_data="continue_from_event_selection")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu_from_transfer_event_selection") # Уникальный коллбэк для возврата из выбора событий трансфера
    )
    builder.adjust(1) # Все кнопки по одной в ряд
    return builder.as_markup()

def get_combined_point_date_keyboard(event_id: str, add_back_button: bool = True) -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для выбора места сдачи/получения и даты в одном шаге.
    Кнопки будут иметь формат "ДД.ММ [Краткое название точки]" или "ДД.ММ - ДД.ММ [Краткое название точки]".
    """
    builder = InlineKeyboardBuilder()
    event_data = None
    if not TRANSFER_CONFIG or 'events' not in TRANSFER_CONFIG:
        logger.error("TRANSFER_CONFIG или ключ 'events' не найден в keyboards.py для combined keyboard.")
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Нет доступных опций", callback_data="no_options_config_error")]])

    for event in TRANSFER_CONFIG['events']:
        if str(event.get('id')) == str(event_id): # Убедимся, что сравниваем строки
            event_data = event
            break

    if not event_data:
        logger.error(f"Событие с ID '{event_id}' не найдено в конфигурации для get_combined_point_date_keyboard.")
        return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Нет доступных опций", callback_data="no_options_event_not_found")]])

    all_combined_options = []

    # Добавляем опции сдачи
    drop_off_options = event_data.get('delivery_options', []) # ИСПРАВЛЕНИЕ: Используем 'delivery_options' вместо 'drop_off_options'
    for point_idx, point in enumerate(drop_off_options):
        point_name_short = point['point_name'].split('(')[0].strip() # Берем только часть до скобок
        if "Староватутинский" in point_name_short:
            point_name_short = "Староватутинский пр-д 12с13"
        elif "Крылатская" in point_name_short or "Прием перед стартом" in point_name_short:
            point_name_short = "Крылатская д.10, Велотрек"
        elif "по вашему адресу" in point_name_short:
            point_name_short = "Доставка"

        for date_str, times in point['available_slots'].items():
            if times: # Убедимся, что есть доступные слоты на эту дату
                try:
                    # ИСПРАВЛЕНИЕ: Новая логика для обработки одного диапазона дат
                    if " - " in date_str:
                        # Обрабатываем диапазон дат
                        start_date_str, end_date_str = date_str.split(' - ')
                        formatted_text = (
                            f"{datetime.strptime(start_date_str, '%Y-%m-%d').strftime('%d.%m')} - "
                            f"{datetime.strptime(end_date_str, '%Y-%m-%d').strftime('%d.%m')} "
                            f"{point_name_short}"
                        )
                    else:
                        # Обрабатываем одиночную дату, как и раньше
                        formatted_text = f"{datetime.strptime(date_str, '%Y-%m-%d').strftime('%d.%m')} {point_name_short}"

                    all_combined_options.append({
                        "text": formatted_text,
                        "callback_data": f"select_combined_dropoff_{event_id}_{point_idx}_{date_str}"
                    })
                except ValueError as ve:
                    logger.error(f"Ошибка форматирования даты '{date_str}' в config.json для события {event_id}, точки {point_idx}: {ve}")
                    continue

    # Сортируем опции по дате для лучшей читаемости
    def sort_key(option):
        try:
            full_callback_data = option['callback_data']
            # Извлекаем дату, используя rsplit('_', 1) для надежного получения последней части
            date_part_from_callback = full_callback_data.rsplit('_', 1)[1]

            # ИСПРАВЛЕНИЕ: Теперь мы можем получать либо одиночную дату, либо диапазон.
            # Для сортировки нам нужна только начальная дата диапазона.
            if " - " in date_part_from_callback:
                date_part_from_callback = date_part_from_callback.split(' - ')[0]

            return datetime.strptime(date_part_from_callback, "%Y-%m-%d")
        except (ValueError, IndexError) as e:
            logger.error(f"sort_key: Ошибка парсинга даты из callback_data '{option['callback_data']}': {e}", exc_info=True)
            return datetime(1900, 1, 1)
        except Exception as e:
            logger.error(f"sort_key: Неожиданная ошибка при сортировке из callback_data '{option['callback_data']}': {e}", exc_info=True)
            return datetime(1900, 1, 1)

    all_combined_options.sort(key=sort_key)


    for option in all_combined_options:
        builder.button(text=option['text'], callback_data=option['callback_data'])

    builder.adjust(1) # Кнопки в один столбец для лучшей читаемости

    if add_back_button:
        _add_back_button(builder, callback_data="back_to_choosing_event") # Возврат к выбору события
    return builder.as_markup()


def get_repair_keyboard(add_back_button: bool = True) -> InlineKeyboardMarkup:
    """
    Клавиатура для вопроса о ремонте.
    Согласно новому плану, кнопки будут "Нет, не требуется" и "⬅️ Назад".
    Пользователь вводит текст, если нужен комментарий.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="Нет, не требуется", callback_data="repair_no_required"))
    if add_back_button:
        logger.debug("get_repair_keyboard: add_back_button is True, calling _add_back_button.")
        _add_back_button(builder, callback_data="back_to_choosing_combined_point_date")
    else:
        logger.debug("get_repair_keyboard: add_back_button is False, not adding back button.")
    return builder.as_markup()

def get_confirmation_keyboard(is_user_registered: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура для финального подтверждения или регистрации.
    :param is_user_registered: True, если пользователь зарегистрирован в системе.
    """
    builder = InlineKeyboardBuilder()
    if is_user_registered:
        builder.row(InlineKeyboardButton(text="✅ Оформить", callback_data="confirm_application"))
    else:
        builder.row(InlineKeyboardButton(text="📝 Регистрация", callback_data="start_registration_from_summary"))

    # Добавляем кнопку "Назад" и "Отменить"
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_repair_question"), # Назад к вопросу о ремонте
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_application")
    )
    builder.adjust(1) # Кнопки в один столбец
    return builder.as_markup()
