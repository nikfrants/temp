# bot_logic/common/keyboards.py
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

# !!! ВАЖНО: Если ваш config.json находится в bot_logic/transfer/config.py
# !!! тогда импорт должен быть такой:

# Если ваш config.json находится в корне проекта или в другом месте,
# раскомментируйте и настройте соответствующий путь:
# with open('config.json', 'r', encoding='utf-8') as f:
#    config = json.load(f)


def _add_back_button(builder: InlineKeyboardBuilder, callback_data: str = "back") -> None:
    """Добавляет кнопку 'Назад' в InlineKeyboardBuilder."""
    builder.row(InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data))


# --- Основные функции для клавиатур ---

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Возвращает главное меню бота с кнопками:
    - Подать заявку на трансфер
    - Зарегистрироваться в BikeCase
    - О BikeCase.ru
    """
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🚀 Подать заявку на трансфер", callback_data="start_transfer_flow"))
    builder.row(InlineKeyboardButton(text="📝 Зарегистрироваться в BikeCase", callback_data="start_registration"))
    builder.row(InlineKeyboardButton(text="ℹ️ О BikeCase.ru", callback_data="about_bikecase"))
    builder.adjust(1)
    return builder.as_markup()


def get_about_bikecase_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для информации "О BikeCase.ru" с кнопкой "Назад".
    """
    builder = InlineKeyboardBuilder()
    _add_back_button(builder, callback_data="back_to_main_menu_from_about")
    return builder.as_markup()

