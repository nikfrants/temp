from __future__ import annotations
import logging
import re  # Для валидации даты

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hbold
from aiogram.filters import StateFilter  # Добавляем импорт StateFilter

# Import for FSM states
from bot_logic.registration.fsm import RegistrationFSM
from bot_logic.common.fsm import CommonFSM  # Для возврата в главное меню
from bot_logic.transfer.fsm import \
    TransferFSM  # Для возврата в сводку трансфера, если регистрация была инициирована оттуда

# Imports for keyboards
from bot_logic.registration import keyboards as registration_kb
from bot_logic.common import keyboards as common_kb  # Для главного меню
from database import db_stubs

# ИМПОРТ НОВОГО КЛАССА ДЛЯ РАБОТЫ С БАЗОЙ КЛИЕНТОВ
from database.clients_excel_db import ClientsExcelManager
# ИМПОРТ ФУНКЦИИ ИЗ TRANSFER_HANDLERS для возврата в сводку
from bot_logic.transfer.handlers import show_final_summary  # Импортируем функцию show_final_summary

# Инициализация менеджера базы клиентов. Путь к файлу жестко задан здесь.
clients_db = ClientsExcelManager(file_path='database/data/clients.xlsx')

router = Router()
logger = logging.getLogger(__name__)


# --- ОБРАБОТЧИК: Отмена регистрации (из любого состояния RegistrationFSM) ---
@router.callback_query(StateFilter(RegistrationFSM), F.data == "cancel_registration")
async def cancel_registration_flow(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Отмена регистрации от пользователя {callback.from_user.id} из состояния {await state.get_state()}")
    await state.clear()
    await callback.message.edit_text(
        "❌ Регистрация отменена. Вы можете начать заново из главного меню.",
        reply_markup=common_kb.get_main_menu_keyboard()
    )
    await state.set_state(CommonFSM.main_menu)
    await callback.answer()


# --- ОБРАБОТЧИК: Начало регистрации по callback_data "start_registration" ---
@router.callback_query(F.data == "start_registration")
async def start_registration_from_menu(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Начало регистрации от пользователя {callback.from_user.id}.")
    await state.set_state(RegistrationFSM.entering_full_name)
    await callback.message.edit_text(
        "Для оформления заявки вам необходимо зарегистрироваться.\\n"
        "Пожалуйста, введите ваше полное имя (Фамилия Имя Отчество):",
        reply_markup=registration_kb.get_registration_start_keyboard()
    )
    await callback.answer()


# --- ОБРАБОТЧИК: Обработка полного имени ---
@router.message(RegistrationFSM.entering_full_name, F.text)
async def process_full_name(message: Message, state: FSMContext):
    full_name = message.text.strip()
    # Простая валидация: имя состоит из 2-3 слов
    if len(full_name.split()) < 2:
        await message.answer("❌ Пожалуйста, введите полное имя (например, 'Иванов Иван Иванович').")
        return

    await state.update_data(full_name=full_name)
    await state.set_state(RegistrationFSM.entering_phone_number)
    await message.answer(
        "Спасибо! Теперь введите ваш номер телефона или поделитесь им с помощью кнопки ниже:",
        reply_markup=registration_kb.get_phone_number_keyboard()
    )


# --- ОБРАБОТЧИК: Обработка номера телефона ---
@router.message(RegistrationFSM.entering_phone_number, F.contact | F.text)
async def process_phone_number(message: Message, state: FSMContext):
    phone_number = message.contact.phone_number if message.contact else message.text
    phone_number = ''.join(filter(str.isdigit, phone_number))

    if not phone_number or len(phone_number) < 10:
        await message.answer("❌ Пожалуйста, введите корректный номер телефона.")
        return

    await state.update_data(phone_number=phone_number)
    await state.set_state(RegistrationFSM.entering_passport_series_number)
    await message.answer(
        "Спасибо! Теперь введите серию и номер паспорта (например, '1234 567890'):",
        reply_markup=ReplyKeyboardRemove()
    )


# --- ОБРАБОТЧИК: Обработка серии и номера паспорта ---
@router.message(RegistrationFSM.entering_passport_series_number, F.text)
async def process_passport_series_number(message: Message, state: FSMContext):
    passport_series_number = message.text.strip()
    if not re.match(r'^\d{4}\s\d{6}$', passport_series_number):
        await message.answer("❌ Пожалуйста, введите серию и номер паспорта в формате '1234 567890'.")
        return

    await state.update_data(passport_series_number=passport_series_number)
    await state.set_state(RegistrationFSM.entering_passport_issued_by)
    await message.answer("Спасибо! Теперь введите, кем выдан паспорт:")


# --- ОБРАБОТЧИК: Обработка 'кем выдан' ---
@router.message(RegistrationFSM.entering_passport_issued_by, F.text)
async def process_passport_issued_by(message: Message, state: FSMContext):
    passport_issued_by = message.text.strip()
    if len(passport_issued_by) < 10:  # Простая валидация
        await message.answer("❌ Пожалуйста, введите полное наименование органа, выдавшего паспорт.")
        return

    await state.update_data(passport_issued_by=passport_issued_by)
    await state.set_state(RegistrationFSM.entering_passport_date_of_issue)
    await message.answer("Спасибо! Теперь введите дату выдачи паспорта (например, '12.01.2023'):")


# --- ОБРАБОТЧИК: Обработка даты выдачи паспорта ---
@router.message(RegistrationFSM.entering_passport_date_of_issue, F.text)
async def process_passport_date_of_issue(message: Message, state: FSMContext):
    passport_date_of_issue = message.text.strip()
    if not re.match(r'^\d{2}\.\d{2}\.\d{4}$', passport_date_of_issue):
        await message.answer("❌ Пожалуйста, введите дату в формате 'ДД.ММ.ГГГГ'.")
        return

    await state.update_data(passport_date_of_issue=passport_date_of_issue)
    await state.set_state(RegistrationFSM.entering_registration_address)
    await message.answer("Спасибо! Теперь введите ваш адрес регистрации:")


# --- ОБРАБОТЧИК: Обработка адреса регистрации и завершение регистрации ---
@router.message(RegistrationFSM.entering_registration_address, F.text)
async def process_address(message: Message, state: FSMContext):
    logger.info(f"User {message.from_user.id} entered registration address.")
    user_id = message.from_user.id
    await state.update_data(registration_address=message.text)

    # Get all the user data from FSM context
    user_data = await state.get_data()

    # Prepare the data to be saved in the client database
    client_data = {
        'user_id': user_id,
        'full_name': user_data.get('full_name'),
        'phone_number': user_data.get('phone_number'),
        'passport_series_number': user_data.get('passport_series_number'),
        'passport_issued_by': user_data.get('passport_issued_by'),
        'passport_date_of_issue': user_data.get('passport_date_of_issue'),
        'registration_address': user_data.get('registration_address'),
    }

    # Use the save_or_update_user method to handle both new and existing users
    if await db_stubs.create_or_update_user(user_id, client_data):
        logger.info(f"User {user_id} successfully registered/updated in Excel DB.")

        # Update the user stub database as well
        await db_stubs.create_or_update_user(user_id, client_data)

        await message.answer(
            "Спасибо! Вы успешно зарегистрированы в BikeCase.",
            reply_markup=ReplyKeyboardRemove()
        )

        # Check if we need to return to the transfer summary after registration
        if user_data.get('return_to_transfer_summary'):
            logger.debug("Returning to transfer summary after successful registration.")
            # Call show_final_summary to display the application summary
            await show_final_summary(message, state)
        else:
            # If not, return to the main menu
            logger.debug("Returning to main menu after successful registration (not from transfer summary).")
            # Get updated user data to show the full name in the greeting
            registered_user_data = await db_stubs.get_user(user_id)
            text = f"С возвращением, {hbold(registered_user_data['full_name'])}! Выберите действие:"
            await message.answer(
                text,
                reply_markup=common_kb.get_main_menu_keyboard(),
                parse_mode="HTML"
            )
            await state.set_state(CommonFSM.main_menu)
    else:
        logger.error(f"Failed to save/update user {user_id} in Excel DB.")
        await message.answer(
            "Произошла ошибка при сохранении данных. Пожалуйста, попробуйте еще раз."
        )
        await state.set_state(RegistrationFSM.entering_registration_address)
