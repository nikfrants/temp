# bot_logic/common/handlers.py
from __future__ import annotations
import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.markdown import hbold, hlink

# Import for FSM states
from oldbot.bot_logic.common.fsm import CommonFSM
from oldbot.bot_logic.transfer.fsm import TransferFSM
from oldbot.bot_logic.registration.fsm import RegistrationFSM

# Imports for keyboards
from oldbot.bot_logic.common import keyboards as common_kb
from oldbot.bot_logic.registration import keyboards as registration_kb

# Import TRANSFER_CONFIG (если он нужен для общих сообщений, иначе удалить)

# Imports for database
from oldbot.database import db_stubs

router = Router()
logger = logging.getLogger(__name__)


# --- ОБРАБОТЧИК /start ---
@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    logger.info(f"Пользователь {message.from_user.id} запустил бота командой /start")
    await state.clear() # Очищаем состояние при старте

    user_data = await db_stubs.get_user(message.from_user.id)

    # Проверяем, зарегистрирован ли пользователь со всеми необходимыми данными
    if user_data and user_data.get('full_name') and user_data.get('phone_number') \
            and user_data.get('passport_series_number') and user_data.get('passport_issued_by') \
            and user_data.get('passport_date_of_issue') and user_data.get('registration_address'):
        text = f"С возвращением, {hbold(user_data['full_name'])}! Выберите действие:"
        reply_markup = common_kb.get_main_menu_keyboard()
    else:
        # Если пользователь не зарегистрирован или его данные неполные
        text = (
            "Здравствуйте! Это бот для оформления заявок на трансфер велосипедов.\n\n"
            "Для полного доступа к функционалу и возможности оформления трансфера, пожалуйста, пройдите регистрацию. "
            "Это позволит нам сформировать все необходимые документы автоматически.\n\n"
            "Выберите действие:"
        )
        reply_markup = common_kb.get_main_menu_keyboard() # Показываем основное меню, где есть кнопка "Зарегистрироваться"

    await message.answer(
        text,
        reply_markup=reply_markup,
        parse_mode="HTML"
    )
    await state.set_state(CommonFSM.main_menu)


# --- ОБРАБОТЧИК /exit ---
@router.message(Command("exit"))
async def cmd_exit(message: Message, state: FSMContext):
    logger.info(f"Получена команда /exit от пользователя {message.from_user.id}")
    await state.clear()

    user_data = await db_stubs.get_user(message.from_user.id)
    text = f"Операция отменена. С возвращением, {hbold(user_data['full_name'])}! Выберите действие:" if user_data else "Операция отменена. Выберите действие:"

    await message.answer(
        text,
        reply_markup=common_kb.get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(CommonFSM.main_menu)


# --- ОБРАБОТЧИК /cancel ---
@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    logger.info(f"Получена команда /cancel от пользователя {message.from_user.id}")
    await state.clear()

    user_data = await db_stubs.get_user(message.from_user.id)
    text = f"Операция отменена. С возвращением, {hbold(user_data['full_name'])}! Выберите действие:" if user_data else "Операция отменена. Выберите действие:"

    await message.answer(
        text,
        reply_markup=common_kb.get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(CommonFSM.main_menu)


# --- ОБРАБОТЧИК КНОПКИ "Зарегистрироваться в BikeCase" (из главного меню) ---
@router.callback_query(CommonFSM.main_menu, F.data == "start_registration")
async def start_registration_flow_from_main_menu(callback: CallbackQuery, state: FSMContext):
    logger.info(f"Начата регистрация из главного меню от пользователя {callback.from_user.id}")
    await state.clear() # Очищаем предыдущее состояние

    # Проверка, зарегистрирован ли пользователь полностью
    user_data_db = await db_stubs.get_user(callback.from_user.id)
    if user_data_db and user_data_db.get('full_name') and user_data_db.get('phone_number') \
            and user_data_db.get('passport_series_number') and user_data_db.get('passport_issued_by') \
            and user_data_db.get('passport_date_of_issue') and user_data_db.get('registration_address'):

        await callback.message.edit_text(
            f"Вы уже зарегистрированы как {hbold(user_data_db['full_name'])}. Выберите действие:",
            reply_markup=common_kb.get_main_menu_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(CommonFSM.main_menu)
        await callback.answer()
        return

    # Если пользователь не зарегистрирован или его данные неполные, начинаем процесс регистрации
    await state.set_state(RegistrationFSM.entering_full_name)
    await callback.message.edit_text(
        "Для регистрации, пожалуйста, введите ваше полное имя (Фамилия Имя Отчество):",
        reply_markup=registration_kb.get_registration_start_keyboard(add_back_button=True),
        parse_mode="HTML"
    )
    await callback.answer()


# --- ОБРАБОТЧИК КНОПКИ "О BikeCase.ru" ---
@router.callback_query(CommonFSM.main_menu, F.data == "about_bikecase")
async def show_about_bikecase(callback: CallbackQuery, state: FSMContext):
    about_text = (
        f"{hbold('О BikeCase.ru')}\n\n"
        "BikeCase.ru — это ваш надежный партнер по трансферу велосипедов на спортивные мероприятия. "
        "Мы обеспечиваем безопасную и своевременную доставку вашего двухколесного друга до места старта "
        "и обратно, чтобы вы могли сосредоточиться исключительно на гонке.\n\n"
        "Наши преимущества:\n"
        "•   Бережная упаковка и транспортировка\n"
        "•   Пунктуальность и надежность\n"
        "•   Удобный сервис оформления заявок\n\n"
        f"Узнайте больше на нашем сайте: {hlink('BikeCase.ru', 'https://bikecase.ru/')}\n\n"
        "Мы всегда готовы помочь вам с логистикой, чтобы ваш старт был максимально комфортным!"
    )
    await callback.message.edit_text(
        about_text,
        reply_markup=common_kb.get_about_bikecase_keyboard(),
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    await state.set_state(CommonFSM.info_about_bikecase)
    await callback.answer()


# --- ОБРАБОТЧИК КНОПКИ "Назад" из "О BikeCase.ru" ---
@router.callback_query(CommonFSM.info_about_bikecase, F.data == "back_to_main_menu_from_about")
async def back_from_about_to_main_menu(callback: CallbackQuery, state: FSMContext):
    user_data = await db_stubs.get_user(callback.from_user.id)
    text = f"С возвращением, {hbold(user_data['full_name'])}! Выберите действие:" if user_data else "Здравствуйте! Это бот для оформления заявок на трансфер велосипедов. Выберите действие:"
    await callback.message.edit_text(
        text,
        reply_markup=common_kb.get_main_menu_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(CommonFSM.main_menu)
    await callback.answer()


# --- ОБЩИЙ ОбрабоТчик для случаев, когда пользователь находится в неправильном состоянии или вводит текст ---
@router.message(F.text)
async def handle_text_input_fallback(message: Message, state: FSMContext):
    current_state = await state.get_state()
    logger.warning(f"Получен текстовый ввод '{message.text}' в состоянии '{current_state}', для которого нет прямого обработчика.")

    expected_text_states = [
        TransferFSM.asking_for_repair,
        RegistrationFSM.entering_full_name,
        RegistrationFSM.entering_phone_number,
        RegistrationFSM.entering_passport_series_number,
        RegistrationFSM.entering_passport_issued_by,
        RegistrationFSM.entering_passport_date_of_issue,
        RegistrationFSM.entering_registration_address,
    ]

    logger.debug(f"Current state: {current_state}, Expected text states: {expected_text_states}")

    if current_state not in expected_text_states:
        await message.reply("Я не понимаю эту команду. Пожалуйста, используйте кнопки или начните заново с /start.")


# --- ОБЩИЙ ОбрабоТчик для остальных коллбэков (для отладки) ---
@router.callback_query()
async def process_unhandled_callbacks(callback: CallbackQuery, state: FSMContext):
    current_state_str = await state.get_state()
    logger.debug(f"Unhandled callback: {callback.data} in state {current_state_str}")
    await callback.answer("Неизвестная команда или действие. Пожалуйста, попробуйте еще раз.", show_alert=True)
