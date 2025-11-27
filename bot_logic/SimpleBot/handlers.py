import json
import logging
from datetime import datetime
import subprocess
import sys
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import (CallbackQuery, FSInputFile, Message)

import keyboards
import texts
from db_functions import check_user_in_db, save_application_to_json
from fsm import ApplicationFSM
from database.excel_manager import main

router = Router()


# --- Обработка команды /start ---
@router.message(Command("start"))
async def start_handler(message: Message, state: FSMContext):
    """
    Обработчик команды /start.
    Проверяет, есть ли пользователь в базе.
    """
    user_id = message.from_user.id
    logging.info(f"Пользователь {user_id} нажал /start")
    if (user_id != 730191569  # Nikolay telegram id main
            and user_id != 233935975
            and user_id != 233935975): # Sergey telegram id
        if 1:
            try:
                await message.bot.send_message(
                    chat_id=6507777374,  # Nikolay telegram id watches
                    text=(f"@{message.from_user.username} {user_id} /start"),
                    parse_mode="HTML"
                )
            except Exception as e:
                logging.error(f"Не удалось отправить уведомление администратору: {e}")



    # Сбрасываем предыдущее состояние, если оно было
    await state.clear()

    if 0:
        # Если пользователь в базе, показываем главное меню
        # await message.answer(texts.MAIN_MENU_TEXT, reply_markup=keyboards.get_main_menu_keyboard())
        await message.answer(texts.MAIN_MENU_TEXT)

        # await state.set_state(ApplicationFSM.main_menu)
    else:
        # Если пользователя нет, начинаем процесс согласия
        # Отправляем файлы
        # offer_document = FSInputFile("/Users/nikfrants/Sync/work/BikeFit Lab/transfer/transfer_tg_bot/bot_logic/SimpleBot/data/Договор_оферты.pdf")
        # pd_agreement_document = FSInputFile("/Users/nikfrants/Sync/work/BikeFit Lab/transfer/transfer_tg_bot/bot_logic/SimpleBot/data/Политика_конфиденциальности.pdf")
        # photo = FSInputFile("/Users/nikfrants/Sync/work/BikeFit Lab/transfer/transfer_tg_bot/bot_logic/SimpleBot/data/photo.jpg")
        offer_document = FSInputFile(
            "D:/sync/2 way BikeFit Lab - nikolay mac/transfer/transfer_tg_bot/bot_logic/SimpleBot/data/Договор_оферты.pdf")
        pd_agreement_document = FSInputFile(
            "D:/sync/2 way BikeFit Lab - nikolay mac/transfer/transfer_tg_bot/bot_logic/SimpleBot/data/Политика_конфиденциальности.pdf")
        photo = FSInputFile(
            "D:/sync/2 way BikeFit Lab - nikolay mac/transfer/transfer_tg_bot/bot_logic/SimpleBot/data/photo.jpg")

        await message.answer_photo(photo, caption=texts.WELCOME_MESSAGE)
        await message.answer_document(offer_document)
        await message.answer_document(pd_agreement_document,
                                      reply_markup=keyboards.get_agreement_keyboard())
        await state.set_state(ApplicationFSM.agreement)


# --- Обработка согласия на обработку ПД ---
@router.callback_query(ApplicationFSM.agreement, F.data == "agree_pd")
async def agreement_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку 'Согласен'.
    """
    await callback.message.edit_reply_markup()  # Убираем кнопки
    await callback.message.answer(texts.MAIN_MENU_TEXT, reply_markup=keyboards.get_main_menu_keyboard())
    await state.set_state(ApplicationFSM.main_menu)
    await callback.answer()


@router.callback_query(ApplicationFSM.agreement, F.data == "disagree_pd")
async def disagreement_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обработчик нажатия на кнопку 'Не согласен'.
    """
    await callback.message.edit_reply_markup()  # Убираем кнопки
    await callback.message.answer(texts.DISAGREEMENT_TEXT)
    await state.clear()
    await callback.answer()


# --- Обработка кнопок главного меню ---
@router.callback_query(ApplicationFSM.main_menu, F.data == "schedule")
async def schedule_handler(callback: CallbackQuery):
    await callback.message.edit_text(texts.SCHEDULE_INFO, reply_markup=keyboards.get_back_to_main_menu_keyboard())
    await callback.answer()


@router.callback_query(ApplicationFSM.main_menu, F.data == "about")
async def about_handler(callback: CallbackQuery):
    await callback.message.edit_text(texts.ABOUT_INFO, reply_markup=keyboards.get_back_to_main_menu_keyboard())
    await callback.answer()

@router.callback_query(ApplicationFSM.main_menu, F.data == "dropoff")
async def dropoff_handler(callback: CallbackQuery):
    await callback.message.edit_text(texts.ENTER_DROPOFF_TEXT, reply_markup=keyboards.get_dropoff_keyboard())
    await callback.answer()

# --- Шаг с ТО: Нажатие кнопок ---
@router.callback_query(ApplicationFSM.selecting_dropoff, F.data.startswith("dropoff_"))
async def selecting_dropoff_handler(callback: CallbackQuery, state: FSMContext):
    dropoff_point = callback.data.split("_")[2]
    comment = "Крыло" if dropoff_point == "krylo" else "Староватут"
    await state.update_data(dropoff=dropoff_point, dropoff_comment=comment)

    await callback.message.edit_text(texts.TECH_SERVICE_TEXT, reply_markup=keyboards.get_tech_service_keyboard())
    await state.set_state(ApplicationFSM.selecting_date)
    await callback.answer()


# --- Начало процесса подачи заявки ---
@router.callback_query(ApplicationFSM.main_menu, F.data == "create_application")
async def create_application_handler(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(texts.ENTER_DROPOFF_TEXT, reply_markup=keyboards.get_dropoff_keyboard())
    await state.set_state(ApplicationFSM.selecting_dropoff)
    await callback.answer()


# --- Выбор даты ---
@router.callback_query(ApplicationFSM.selecting_date, F.data.startswith("date_"))
async def date_selection_handler(callback: CallbackQuery, state: FSMContext):
    selected_date = callback.data.split("_")[1]
    await state.update_data(selected_date=selected_date)
    await callback.message.edit_text(texts.TECH_SERVICE_TEXT, reply_markup=keyboards.get_tech_service_keyboard())
    await state.set_state(ApplicationFSM.tech_service)
    await callback.answer()


# --- Шаг с ТО: Нажатие кнопок ---
@router.callback_query(ApplicationFSM.tech_service, F.data.startswith("service_"))
async def tech_service_button_handler(callback: CallbackQuery, state: FSMContext):
    service_needed = callback.data.split("_")[1]
    comment = "Не требуется" if service_needed == "нет" else "Требуется"
    await state.update_data(tech_service=service_needed, tech_service_comment=comment)

    await callback.message.edit_text(texts.ENTER_FIO_TEXT, reply_markup=keyboards.get_back_button("tech_service"))
    await state.set_state(ApplicationFSM.entering_fio)
    await callback.answer()



# --- Шаг с ТО: Ввод текста ---
@router.message(ApplicationFSM.tech_service)
async def tech_service_text_handler(message: Message, state: FSMContext):
    await state.update_data(tech_service="да", tech_service_comment=message.text)

    await message.answer(texts.ENTER_FIO_TEXT, reply_markup=keyboards.get_back_button("tech_service"))
    await state.set_state(ApplicationFSM.entering_fio)


# --- Ввод персональных данных ---
@router.message(ApplicationFSM.entering_fio)
async def fio_handler(message: Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await message.answer(texts.ENTER_PHONE_TEXT, reply_markup=keyboards.get_back_button("entering_fio"))
    await state.set_state(ApplicationFSM.entering_phone)


@router.message(ApplicationFSM.entering_phone)
async def phone_handler(message: Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await message.answer(texts.ENTER_ADDRESS_TEXT, reply_markup=keyboards.get_back_button("entering_phone"))
    await state.set_state(ApplicationFSM.entering_address)


@router.message(ApplicationFSM.selecting_dropoff)
async def phone_handler(message: Message, state: FSMContext):
    await state.update_data(dropoff_point=message.text)
    await message.answer(texts.ENTER_DROPOFF_TEXT, reply_markup=keyboards.get_back_button("selecting_dropoff"))
    await state.set_state(ApplicationFSM.entering_address)


@router.message(ApplicationFSM.entering_address)
async def address_handler(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await message.answer(texts.ENTER_PASSPORT_TEXT, reply_markup=keyboards.get_back_button("entering_address"))
    await state.set_state(ApplicationFSM.entering_passport)


@router.message(ApplicationFSM.entering_passport)
async def passport_handler(message: Message, state: FSMContext):
    await state.update_data(passport=message.text)

    # --- Подведение итогов ---
    user_data = await state.get_data()
    summary = texts.get_summary_text(user_data)

    await message.answer(summary, reply_markup=keyboards.get_confirmation_keyboard())
    await state.set_state(ApplicationFSM.final_confirmation)


# --- Финальное подтверждение ---
@router.callback_query(ApplicationFSM.final_confirmation, F.data == "confirm")
async def confirm_application_handler(callback: CallbackQuery, state: FSMContext):
    user_data = await state.get_data()
    user_info = {
        'user_id': callback.from_user.id,
        'timestamp': datetime.now().isoformat(),
        'date': user_data.get('selected_date'),
        "event_name": 'Сочи 2025',
        'tech_service_needed': user_data.get('tech_service'),
        'tech_service_comment': user_data.get('tech_service_comment'),
        'full_name': user_data.get('fio'),
        'phone': user_data.get('phone'),
        'address': user_data.get('address'),
        'passport': user_data.get('passport', 'Не указаны'),
        'dropoff_point': user_data.get('dropoff_point'),
    }

    await save_application_to_json(user_info)
    if user_data.get('selected_date', 'Не указана') == '23-29-starovatut':
        date = '      23.09 - 29.09 11:00-20:00\n      Староватутинский пр. 12с13'
    elif user_data.get('selected_date', 'Не указана') == '27-krylo':
        date = '      27.09 11:00-20:00\n      Крылатская ул. д.10'
    elif user_data.get('selected_date', 'Не указана') == '28-krylo':
        date = '      28.09 11:00-20:00\n      Крылатская ул. д.10'
    else:
        date = 'Не указано'
    # Формируем сообщение для администратора
    admin_message = (
        "<b>🚴 Новая заявка на трансфер!</b>\n\n"
        # "<b>🚴 Новая заявка в лист ожидания!</b>\n\n"
        f"👤 <b>Клиент:</b> {user_data.get('fio', 'Не указано')}\n"
        f"📞 <b>Телефон:</b> {user_data.get('phone', 'Не указан')}\n"
        f"📅 <b>Дата сдачи:</b> \n{date}\n"
        f"🔧 <b>ТО:</b> {user_data.get('tech_service_comment', 'Не указано')}\n\n"
        f"🏠 <b>Адрес:</b> {user_data.get('address', 'Не указан')}\n"
        f"🛂 <b>Паспортные данные:</b> {user_data.get('passport', 'Не указаны')}\n\n"
        f"🛂 <b>Точка сдачи:</b> {user_data.get('dropoff_point', 'Не указаны')}\n\n"
        
        f"userID {callback.from_user.id}\n\n"
        f"Написать в телеграм @{callback.from_user.username}"
    )
    # Формируем сообщение для администратора
    user_message = (
        "<b>Ваша заявка принята!</b>\nДля подтверждения бронирования менеджер свяжется с вами в ближайшее время.\n"
        "<b>Вопросы по бронированию можно задать по телефону:\n+7 910 490 4444.\n\n"
        "❗️Подписание и оплата договора при сдаче велосипеда.</b>\n\n"
        # "<b>Вы добавлены в лист ожидания!\n</b>\n\n"
        "🚴 <b>Трансфер в Сириус Сочи:</b>\n"
        f"📅 <b>Дата сдачи велосипеда:</b>\n{date}\n"
        f"🔧 <b>ТО:</b> {user_data.get('tech_service_comment', 'Не указано')}\n\n"
        f"👤 <b>ФИО:</b> {user_data.get('fio', 'Не указано')}\n"
        f"📞 <b>Телефон:</b> {user_data.get('phone', 'Не указан')}\n"
        f"🏠 <b>Адрес:</b> {user_data.get('address', 'Не указан')}\n"
        f"🛂 <b>Паспортные данные:</b> \n      {user_data.get('passport', 'Не указаны')}\n\n"
    )

    # Отправляем сообщение администратору
    if 0:
        try:
            await callback.bot.send_message(
                chat_id=233935975,  # Sergei telegram id
                text=admin_message,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление администратору: {e}")
    if 1:
        try:
            await callback.bot.send_message(
                chat_id=730191569,  # Nikolay telegram id
                text=admin_message,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Не удалось отправить уведомление администратору: {e}")


    #    await callback.message.edit_text(texts.APPLICATION_SUCCESS_TEXT)
    await callback.message.edit_text(user_message)
    await callback.message.answer(texts.MAIN_MENU_TEXT, reply_markup=keyboards.get_main_menu_keyboard())
    await state.set_state(ApplicationFSM.main_menu)
    await callback.answer("Заявка успешно создана!\nДля подтверждения бронирования менеджер свяжется с Вами в ближайшее время.", show_alert=True)
    # await callback.answer("Вы успешно добавлены в лист ожидания!", show_alert=True)
    # script_path = "C:/Users/Nikolay/PycharmProjects/transfer_tg_bot/database/excel_manager.py"
    script_path = "D:/sync/2 way BikeFit Lab - nikolay mac/transfer/transfer_tg_bot/database/excel_manager.py"
    subprocess.run([sys.executable, script_path])


# --- Универсальный обработчик кнопки "Назад" ---
@router.callback_query(F.data.startswith("back_to_"))
async def back_button_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает все нажатия на кнопки "Назад".
    """
    action = callback.data.split("back_to_")[1]
    logging.info(f"Нажата кнопка 'Назад' к шагу: {action}")

    # Убираем клавиатуру у текущего сообщения
    await callback.message.edit_reply_markup()

    if action == "main_menu":
        await callback.message.answer(texts.MAIN_MENU_TEXT, reply_markup=keyboards.get_main_menu_keyboard())
        await state.set_state(ApplicationFSM.main_menu)
    elif action == "selecting_dropoff":
        await callback.message.answer(texts.CHOOSE_DATE_TEXT, reply_markup=keyboards.get_back_button("main_menu"))
        await state.set_state(ApplicationFSM.selecting_dropoff)
    elif action == "selecting_date":
        await callback.message.answer(texts.CHOOSE_DATE_TEXT, reply_markup=keyboards.get_dropoff_keyboard())
        await state.set_state(ApplicationFSM.selecting_date)
    elif action == "tech_service":
        await callback.message.answer(texts.TECH_SERVICE_TEXT, reply_markup=keyboards.get_tech_service_keyboard())
        await state.set_state(ApplicationFSM.tech_service)
    elif action == "entering_fio":
        await callback.message.answer(texts.ENTER_FIO_TEXT, reply_markup=keyboards.get_back_button("tech_service"))
        await state.set_state(ApplicationFSM.entering_fio)
    elif action == "entering_phone":
        await callback.message.answer(texts.ENTER_PHONE_TEXT, reply_markup=keyboards.get_back_button("entering_fio"))
        await state.set_state(ApplicationFSM.entering_phone)
    elif action == "entering_address":
        await callback.message.answer(texts.ENTER_ADDRESS_TEXT,
                                      reply_markup=keyboards.get_back_button("entering_phone"))
        await state.set_state(ApplicationFSM.entering_address)

    await callback.answer()
