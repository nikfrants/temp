from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.markdown import hbold
from datetime import datetime

def _add_back_button(builder: InlineKeyboardBuilder, callback_data: str = "back") -> None:
    """
    Добавляет кнопку '⬅️ Назад' в InlineKeyboardBuilder.
    """
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data))

def format_application_summary(user_data: dict) -> str:
    """
    Формирует сводку заявки на основе данных пользователя.
    Исключает личные данные пользователя (ФИО, телефон, паспорт, адрес),
    оставляя только информацию, относящуюся к самой заявке.
    """
    summary_parts = []

    # Данные, относящиеся к заявке
    event_name = user_data.get('event_name')
    point_name = user_data.get('selected_point_name')
    date = user_data.get('selected_date')
    time = user_data.get('selected_time') # Это "время сдачи" в текущем флоу

    if event_name:
        summary_parts.append(f"<b>Событие:</b> {hbold(event_name)}")
    if point_name:
        summary_parts.append(f"<b>Место сдачи:</b> {hbold(point_name)}")
    if date:
        # Форматируем дату для отображения из YYYY-MM-DD в DD.MM.YYYY
        try:
            formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%d.%m.%Y")
            summary_parts.append(f"<b>Дата сдачи:</b> {hbold(formatted_date)}")
        except ValueError:
            summary_parts.append(f"<b>Дата сдачи:</b> {hbold(date)} (неверный формат)")
    if time:
        summary_parts.append(f"<b>Время сдачи:</b> {hbold(time)}")

    pre_repair = user_data.get('pre_repair')
    pre_repair_comment = user_data.get('pre_repair_comment')

    if pre_repair is not None: # Если значение было установлено
        if pre_repair:
            summary_parts.append(f"<b>Предварительный ремонт:</b> {hbold('Да')}")
            if pre_repair_comment:
                summary_parts.append(f"<b>Комментарий механику:</b> {pre_repair_comment}")
        else:
            summary_parts.append(f"<b>Предварительный ремонт:</b> {hbold('Нет')}")

    return "\\n".join(summary_parts)
