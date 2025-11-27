# bot_logic/admin/common/keyboards.py

from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from oldbot.bot_logic.utils.utils import _add_back_button # Можно использовать _add_back_button

def get_admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Главное меню админки."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Управление трансферами 🚴", callback_data="admin_transfer_menu")
    builder.button(text="Управление арендой 📦", callback_data="admin_rent_menu")
    builder.button(text="Статистика 📊", callback_data="admin_stats")
    builder.adjust(1)
    return builder.as_markup()

def get_back_to_admin_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Кнопка для возврата в главное меню админки."""
    builder = InlineKeyboardBuilder()
    _add_back_button(builder, callback_data="back_to_admin_main_menu")
    return builder.as_markup()