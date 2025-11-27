from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_agreement_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для согласия на обработку ПД.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Согласен", callback_data="agree_pd"),
        InlineKeyboardButton(text="❌ Не согласен", callback_data="disagree_pd")
    )
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру главного меню.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📝 Записаться на трансфер", callback_data="create_application"))
    builder.row(
        InlineKeyboardButton(text="🗓️ Расписание", callback_data="schedule"),
        InlineKeyboardButton(text="ℹ️ О BikeCase", callback_data="about")
    )
    return builder.as_markup()



def get_back_to_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру с одной кнопкой "Назад в главное меню".
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu"))
    return builder.as_markup()

def get_dropoff_keyboard():
    """
    Возвращает клавиатуру для выбора точки сдачи велосипеда.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="ул. Крылатская д.10", callback_data=f"dropoff_point_krylo"))
    builder.row(InlineKeyboardButton(text="Староватутинский пр-д. д12с13", callback_data=f"dropoff_point_star"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_main_menu"))
    return builder.as_markup()

def get_date_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для выбора даты.
    """
    builder = InlineKeyboardBuilder()
    # Пример дат. Можно генерировать динамически.
    builder.row(InlineKeyboardButton(text="23-29.09 Староватут. пр. 12с13", callback_data="date_23-29-starovatut"))
    # builder.row(InlineKeyboardButton(text="27.09 Крылатская ул.д.10", callback_data="date_27-krylo"))
    # builder.row(InlineKeyboardButton(text="28.09 Крылатская ул.д.10", callback_data="date_28-krylo"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_selecting_dropoff"))
    return builder.as_markup()


def get_tech_service_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для выбора необходимости ТО.
    """
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="👍 Да", callback_data="service_да"),
        InlineKeyboardButton(text="👎 Нет", callback_data="service_нет")
    )
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_selecting_dropoff"))
    return builder.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает клавиатуру для финального подтверждения.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_entering_address"))
    return builder.as_markup()


def get_back_button(previous_step: str) -> InlineKeyboardMarkup:
    """
    Возвращает универсальную кнопку "Назад".
    :param previous_step: колбэк-данные для возврата на предыдущий шаг.
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"back_to_{previous_step}"))
    return builder.as_markup()


