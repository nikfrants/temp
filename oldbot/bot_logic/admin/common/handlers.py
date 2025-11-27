# bot_logic/admin/common/handlers.py
import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

# Импорты для FSM
from oldbot.bot_logic.admin.common.fsm import AdminCommonFSM
from oldbot.bot_logic.admin.transfer.fsm import AdminTransferFSM # Для перехода в управление трансферами

# Импорты для клавиатур
from oldbot.bot_logic.admin.common import keyboards as admin_common_kb
from oldbot.bot_logic.admin.transfer import keyboards as admin_transfer_kb # Для вызова меню трансферов

# Импорт конфигурации (для получения admin_ids)
from oldbot.bot_logic.transfer.config import TRANSFER_CONFIG # Здесь мы берем admin_ids из общего конфига трансфера

router = Router()
logger = logging.getLogger(__name__)

# --- Обработка входа в меню админ-трансферов ---
@router.callback_query(AdminCommonFSM.admin_main_menu, F.data == 'admin_transfer_menu')
async def admin_transfer_menu(callback: CallbackQuery, state: FSMContext):
    # Дополнительная проверка на админа, хотя уже была при входе в админку
    if callback.from_user.id not in TRANSFER_CONFIG.get('admin_ids', []):
        await callback.answer("У вас нет прав доступа.", show_alert=True)
        await callback.message.delete()
        await state.clear() # Сбрасываем состояние на всякий случай
        return

    await callback.message.edit_text(
        "Выберите действие для управления трансферами:",
        reply_markup=admin_transfer_kb.get_admin_transfer_menu_keyboard()
    )
    await state.set_state(AdminTransferFSM.transfer_management_menu)
    await callback.answer()

# --- Обработка кнопки "Назад" в админке (из подменю в главное меню админки) ---
@router.callback_query(AdminTransferFSM.transfer_management_menu, F.data == 'back_to_admin_main_menu')
async def back_to_admin_main_menu(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Добро пожаловать в админ-панель!",
        reply_markup=admin_common_kb.get_admin_main_menu_keyboard()
    )
    await state.set_state(AdminCommonFSM.admin_main_menu)
    await callback.answer()

# Добавьте здесь другие общие админские хэндлеры (например, для статистики, управления арендой, если они будут)
# @router.callback_query(AdminCommonFSM.admin_main_menu, F.data == 'admin_rent_menu')
# async def admin_rent_menu(callback: CallbackQuery, state: FSMContext):
#    ...