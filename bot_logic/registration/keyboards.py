# bot_logic/registration/keyboards.py

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, \
    ReplyKeyboardRemove  # Импортируем ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_logic.utils.utils import _add_back_button  # Убедитесь, что _add_back_button доступна


def get_phone_number_keyboard() -> ReplyKeyboardMarkup:
    """
    Клавиатура для запроса номера телефона с кнопкой "Поделиться номером телефона".
    Это Reply-клавиатура, которая заменяет стандартную клавиатуру ввода.
    """
    button = KeyboardButton(text="Поделиться номером телефона", request_contact=True)
    # one_time_keyboard=True: клавиатура скрывается после использования
    # resize_keyboard=True: клавиатура подстраивается под высоту экрана
    return ReplyKeyboardMarkup(keyboard=[[button]], resize_keyboard=True, one_time_keyboard=True)


def get_registration_start_keyboard(add_back_button: bool = False) -> InlineKeyboardMarkup:
    """
    Клавиатура для начала регистрации, возможно, с кнопкой отмены и/или "Назад".
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="❌ Отменить регистрацию", callback_data="cancel_registration"))
    builder.adjust(1)  # Кнопки по одной в ряд

    if add_back_button:
        # Эта кнопка "Назад" может быть использована для возврата из регистрации,
        # например, если регистрация была инициирована из сводки заявки.
        _add_back_button(builder, callback_data="back_to_previous_state_from_registration")

    return builder.as_markup()

