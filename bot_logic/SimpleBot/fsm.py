from aiogram.fsm.state import State, StatesGroup


class ApplicationFSM(StatesGroup):
    """
    Класс состояний для процесса подачи заявки.
    """
    selecting_dropoff = State()
    agreement = State()
    main_menu = State()
    selecting_date = State()
    tech_service = State()
    entering_fio = State()
    entering_phone = State()
    entering_address = State()
    entering_passport = State()
    final_confirmation = State()




