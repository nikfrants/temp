# bot_logic/admin/common/fsm.py

from aiogram.fsm.state import State, StatesGroup

class AdminCommonFSM(StatesGroup):
    admin_main_menu = State() # Главное меню админки
    # Добавляйте сюда другие общие админские состояния, если они появятся