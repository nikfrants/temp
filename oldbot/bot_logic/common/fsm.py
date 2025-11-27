# bot_logic/common/fsm.py

from aiogram.fsm.state import State, StatesGroup

class CommonFSM(StatesGroup):
    main_menu = State()          # Главное меню бота (после /start)
    info_about_bikecase = State() # Состояние для информации "О BikeCase.ru"
    # Добавляйте сюда другие общие пользовательские состояния, если они появятся
