# bot_logic/admin/transfer/keyboards.py

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot_logic.utils.utils import _add_back_button


def get_admin_transfer_menu_keyboard() -> InlineKeyboardMarkup:
    """Меню управления трансферами для админа."""
    builder = InlineKeyboardBuilder()
    builder.button(text="Посмотреть заявки 📋", callback_data="admin_view_applications")
    builder.button(text="Создать событие ➕", callback_data="admin_create_event")
    # Добавьте другие кнопки, если нужны (редактирование, удаление событий и т.д.)
    _add_back_button(builder, callback_data="back_to_admin_main_menu")
    return builder.as_markup()


def get_application_list_keyboard(applications: list, page: int = 0, items_per_page: int = 5) -> InlineKeyboardMarkup:
    """Клавиатура для постраничного просмотра заявок."""
    builder = InlineKeyboardBuilder()
    start_index = page * items_per_page
    end_index = start_index + items_per_page

    for i, app in enumerate(applications[start_index:end_index]):
        builder.button(text=f"Заявка №{app['id']} ({app['full_name']})", callback_data=f"admin_view_app_{app['id']}")

    # Кнопки навигации
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_apps_page_{page - 1}"))
    if end_index < len(applications):
        nav_buttons.append(InlineKeyboardButton(text="Вперед ➡️", callback_data=f"admin_apps_page_{page + 1}"))

    if nav_buttons:
        builder.row(*nav_buttons)

    _add_back_button(builder, callback_data="back_to_admin_transfer_menu")
    return builder.as_markup()


def get_application_details_keyboard(application_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для действий с конкретной заявкой."""
    buttons = [
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"admin_edit_app_{application_id}")],
        [InlineKeyboardButton(text="❌ Удалить", callback_data=f"admin_delete_app_{application_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="back_to_admin_view_applications")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)