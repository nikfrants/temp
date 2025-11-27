# bot_logic/admin/transfer/handlers.py
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

# Импорты для FSM
from oldbot.bot_logic.admin.transfer.fsm import AdminTransferFSM

# Импорты для клавиатур
from oldbot.bot_logic.admin.transfer import keyboards as admin_transfer_kb

# Импорты для базы данных

# Импорт утилит
from oldbot.bot_logic.utils.utils import format_application_summary

# Импорт конфигурации (для получения admin_ids)
from oldbot.bot_logic.transfer.config import TRANSFER_CONFIG

router = Router()
logger = logging.getLogger(__name__)


# --- Вспомогательная функция для проверки прав админа ---
def is_admin(user_id: int) -> bool:
    return user_id in TRANSFER_CONFIG.get('admin_ids', [])


# --- Просмотр списка заявок ---
@router.callback_query(AdminTransferFSM.transfer_management_menu, F.data == 'admin_view_applications')
@router.callback_query(AdminTransferFSM.viewing_applications, F.data.startswith('admin_apps_page_'))
async def admin_view_applications(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return

    current_page = 0
    if F.data.startswith('admin_apps_page_'):
        current_page = int(callback.data.split('_')[-1])

    # TODO: Получить реальные заявки из БД
    # Пока заглушка:
    all_applications = [
        {"id": 1, "full_name": "Иванов И.И.", "event_name": "Весенний марафон", "status": "Новая"},
        {"id": 2, "full_name": "Петров А.В.", "event_name": "Гонка Лето 2025", "status": "В обработке"},
        {"id": 3, "full_name": "Сидорова Е.К.", "event_name": "Гонка Осень 2025", "status": "Завершена"},
        {"id": 4, "full_name": "Кузнецов Р.Л.", "event_name": "Весенний марафон", "status": "Новая"},
        {"id": 5, "full_name": "Смирнова В.О.", "event_name": "Гонка Лето 2025", "status": "Отменена"},
        {"id": 6, "full_name": "Волков С.Д.", "event_name": "Гонка Осень 2025", "status": "Новая"},
    ]

    await callback.message.edit_text(
        f"Список заявок (Страница {current_page + 1}):",
        reply_markup=admin_transfer_kb.get_application_list_keyboard(all_applications, current_page)
    )
    await state.set_state(AdminTransferFSM.viewing_applications)
    await callback.answer()


# --- Просмотр деталей конкретной заявки ---
@router.callback_query(AdminTransferFSM.viewing_applications, F.data.startswith('admin_view_app_'))
async def admin_view_app_details(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return

    app_id = int(callback.data.replace('admin_view_app_', ''))

    # TODO: Получить реальные данные заявки из БД по app_id
    # Пока заглушка:
    application_data = {
        "id": app_id,
        "event_name": "Гонка 'Золотые Колеса'",
        "drop_off_point_name": "Точка на Ленина, 1",
        "drop_off_date": "2025-07-10",
        "drop_off_time": "10:00-12:00",
        "pickup_point_name": "Привезём по вашему адресу",
        "pickup_date": "2025-07-21",
        "pickup_time": "10:00-18:00",
        "pre_repair": True,
        "pre_repair_comment": "Требуется замена покрышек и настройка переключателя.",
        "full_name": "Тестовый Тест Тестович",
        "phone_number": "+79001234567",
        "status": "Новая"
    }

    summary_text = format_application_summary(application_data) + f"\nСтатус: {application_data['status']}"

    await callback.message.edit_text(
        f"Детали заявки №{app_id}:\n\n{summary_text}",
        reply_markup=admin_transfer_kb.get_application_details_keyboard(app_id)
    )
    await state.update_data(current_admin_application_id=app_id)  # Сохраняем ID для дальнейших действий
    await state.set_state(AdminTransferFSM.editing_application)  # Переходим в состояние редактирования
    await callback.answer()


# --- Редактирование заявки (начало процесса) ---
@router.callback_query(AdminTransferFSM.editing_application, F.data.startswith('admin_edit_app_'))
async def admin_edit_application(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return

    app_id = int(callback.data.replace('admin_edit_app_', ''))
    # TODO: Здесь будет логика для начала редактирования заявки
    await callback.message.edit_text(f"Редактирование заявки №{app_id} (функционал в разработке).")
    await callback.answer()


# --- Удаление заявки (подтверждение) ---
@router.callback_query(AdminTransferFSM.editing_application, F.data.startswith('admin_delete_app_'))
async def admin_delete_application_confirm(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return

    app_id = int(callback.data.replace('admin_delete_app_', ''))
    # TODO: Здесь будет клавиатура с подтверждением удаления
    await callback.message.edit_text(f"Вы уверены, что хотите удалить заявку №{app_id}?",
                                     reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                         [InlineKeyboardButton(text="Да, удалить",
                                                               callback_data=f"admin_confirm_delete_app_{app_id}")],
                                         [InlineKeyboardButton(text="Нет, отмена",
                                                               callback_data="back_to_admin_app_details")]
                                     ]))
    await state.set_state(AdminTransferFSM.deleting_application)
    await callback.answer()


# --- Удаление заявки (окончательное) ---
@router.callback_query(AdminTransferFSM.deleting_application, F.data.startswith('admin_confirm_delete_app_'))
async def admin_delete_application_execute(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return

    app_id = int(callback.data.replace('admin_confirm_delete_app_', ''))
    # TODO: Реальная логика удаления из БД
    logger.info(f"ЗАГЛУШКА: Удаление заявки №{app_id} из БД.")
    await callback.message.edit_text(f"Заявка №{app_id} успешно удалена.")
    await state.set_state(AdminTransferFSM.transfer_management_menu)  # Возвращаемся в меню управления трансферами
    await callback.answer()


# --- Возврат из деталей заявки к списку ---
@router.callback_query(AdminTransferFSM.editing_application, F.data == 'back_to_admin_app_details')
@router.callback_query(AdminTransferFSM.deleting_application, F.data == 'back_to_admin_app_details')
async def back_to_admin_app_details(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return
    # Снова вызываем функцию просмотра списка, чтобы обновить клавиатуру
    await admin_view_applications(callback, state)  # Возвращаем на текущую страницу списка
    await callback.answer()


# --- Возврат к меню управления трансферами из списка заявок ---
@router.callback_query(AdminTransferFSM.viewing_applications, F.data == 'back_to_admin_transfer_menu')
async def back_to_admin_transfer_menu_from_viewing(callback: CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        return

    await callback.message.edit_text(
        "Выберите действие для управления трансферами:",
        reply_markup=admin_transfer_kb.get_admin_transfer_menu_keyboard()
    )
    await state.set_state(AdminTransferFSM.transfer_management_menu)
    await callback.answer()

# Здесь можно добавить хэндлеры для "Создать событие" и т.д.