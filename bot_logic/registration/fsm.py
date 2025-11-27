# bot_logic/registration/fsm.py
from aiogram.fsm.state import State, StatesGroup

class RegistrationFSM(StatesGroup):
    entering_full_name = State()            # Ввод полного имени
    entering_phone_number = State()         # Ввод номера телефона
    entering_passport_series_number = State() # Ввод серии и номера паспорта
    entering_passport_issued_by = State()   # Ввод кем выдан паспорт
    entering_passport_date_of_issue = State() # Ввод даты выдачи паспорта
    entering_registration_address = State() # Ввод адреса прописки по паспорту
    # Добавляйте сюда другие состояния, если потребуются
