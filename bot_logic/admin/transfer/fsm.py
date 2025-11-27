# bot_logic/admin/transfer/fsm.py

from aiogram.fsm.state import State, StatesGroup

class AdminTransferFSM(StatesGroup):
    transfer_management_menu = State()  # Меню управления трансферами в админке
    viewing_applications = State()      # Просмотр списка заявок
    editing_application = State()       # Редактирование конкретной заявки
    deleting_application = State()      # Удаление заявки
    # ... другие состояния для администрирования трансферов