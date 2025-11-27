# bot_logic/transfer/handlers.py
from __future__ import annotations

import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.markdown import hbold
from aiogram.filters import Command  # ИСПРАВЛЕНИЕ: Добавлен импорт Command

# Импорты для FSM
from oldbot.bot_logic.transfer.fsm import TransferFSM
from oldbot.bot_logic.registration.fsm import RegistrationFSM
from oldbot.bot_logic.common.fsm import CommonFSM

# Импорты для клавиатур
from oldbot.bot_logic.transfer import keyboards as transfer_kb
from oldbot.bot_logic.common import keyboards as common_kb
from oldbot.bot_logic.registration import keyboards as registration_kb

# Импорты для базы данных
from oldbot.database import db_stubs

# Импорт конфигурации трансфера
from oldbot.bot_logic.transfer.config import TRANSFER_CONFIG as config

# Импорт утилит
from oldbot.bot_logic.utils.utils import format_application_summary

router = Router()
logger = logging.getLogger(__name__)


# Вспомогательная функция для получения данных события/точки
def get_event_data(event_id: str):
    """Возвращает словарь с данными события по его ID."""
    if not config or 'events' not in config:
        logger.error("TRANSFER_CONFIG или ключ 'events' не найден. Проверьте config.json и config.py")
        return None
    for event in config['events']:
        # Убедимся, что сравниваем строки, чтобы избежать проблем с типами
        if str(event.get('id')) == str(event_id):
            return event
    logger.warning(f"Событие с ID '{event_id}' не найдено в конфигурации TRANSFER_CONFIG.")
    return None


def get_option_data(event_data: dict, option_type: str, point_index: int):
    """
    Возвращает словарь с данными точки (сдачи или получения) по типу и индексу.
    Исправлена ошибка KeyError, связанная с несоответствием названия ключей в config.json
    (drop_off_options вместо dropoff_options).
    """
    actual_option_key = ""
    if option_type == "dropoff":
        actual_option_key = "drop_off_options"  # Правильный ключ из config.json
    elif option_type == "pickup":
        actual_option_key = "pickup_options"  # Правильный ключ из config.json
    else:
        logger.error(f"Неизвестный тип опции: {option_type}")
        return None

    try:
        # Теперь используем правильный ключ actual_option_key
        return event_data[actual_option_key][point_index]
    except (IndexError, KeyError) as e:
        logger.error(f"Ошибка получения опции '{option_type}' по индексу {point_index} из данных события, "
                     f"используя ключ '{actual_option_key}': {e}", exc_info=True)
        return None


# --- ОБРАБОТЧИК КНОПКИ "Подать заявку на трансфер" (ИЗ ГЛАВНОГО МЕНЮ) ---
@router.callback_query(CommonFSM.main_menu, F.data == "start_transfer_flow")
async def start_transfer_flow(callback: CallbackQuery, state: FSMContext):
    logger.info("Начало флоу трансфера. Загрузка событий.")

    selected_event_id = None
    event_description = "Выберите событие из списка ниже, чтобы увидеть его описание."

    if config and 'events' in config and config['events']:
        # Если есть события, выбираем первое по умолчанию
        first_event = config['events'][0]
        selected_event_id = first_event.get('id')
        event_description = first_event.get('description', event_description)
        logger.debug(f"Первое событие в конфиге: ID={selected_event_id}, Описание: {event_description[:50]}...")
    else:
        event_description = "В данный момент нет доступных событий для трансфера. Пожалуйста, попробуйте позже."
        logger.warning("Нет доступных событий в TRANSFER_CONFIG.events.")

    # Сохраняем выбранное событие в состояние (для дальнейшего использования и для галочки)
    await state.update_data(selected_event_id=selected_event_id)

    # Отправляем сообщение с описанием первого события и клавиатурой выбора событий
    try:
        await callback.message.edit_text(
            event_description,
            reply_markup=transfer_kb.get_events_keyboard(selected_event_id=selected_event_id),
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        logger.error(f"Ошибка TelegramBadRequest при отправке клавиатуры событий: {e}")
        await callback.message.answer("Произошла ошибка при загрузке событий. Пожалуйста, попробуйте еще раз.")
        await state.set_state(CommonFSM.main_menu)  # Возвращаемся в главное меню
        await callback.answer()
        return

    await state.set_state(TransferFSM.choosing_event)  # Переходим в состояние выбора события
    await callback.answer()


# --- ОБРАБОТЧИК: выбор события из списка (при нажатии на кнопку события) ---
@router.callback_query(TransferFSM.choosing_event, F.data.startswith('select_event_'))
async def select_event(callback: CallbackQuery, state: FSMContext):
    # Извлечение event_id: теперь корректно получаем ID после 'select_event_'
    event_id = callback.data.replace('select_event_', '')
    logger.info(f"Выбрано событие с event_id: '{event_id}'")

    user_data = await state.get_data()
    current_selected_event_id = user_data.get('selected_event_id')

    # Проверка, выбрано ли уже это событие
    if event_id == current_selected_event_id:
        await callback.answer("Это событие уже выбрано. Нажмите 'Далее ➡️' для продолжения.", show_alert=True)
        return

    selected_event_data = get_event_data(event_id)

    if selected_event_data:
        # Обновляем состояние выбранным событием
        await state.update_data(selected_event_id=event_id)

        # Обновляем сообщение с новым описанием и клавиатурой с галочкой
        try:
            await callback.message.edit_text(
                selected_event_data.get('description', "Описание события не найдено."),
                reply_markup=transfer_kb.get_events_keyboard(selected_event_id=event_id),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            logger.debug(
                f"TelegramBadRequest при редактировании сообщения (сообщение не изменено или слишком быстро): {e}")
            # Просто отвечаем на коллбэк, если сообщение не изменилось
            pass
    else:
        # Эта ветка должна срабатывать, если get_event_data вернул None
        await callback.answer("Извините, событие не найдено в конфигурации. Возможно, устаревшие данные.",
                              show_alert=True)
        logger.error(f"Не удалось найти данные для выбранного event_id: {event_id} в конфиге.")

    await callback.answer()


# --- ОБРАБОТЧИК КНОПКИ "Далее" после выбора события (Переход к объединенному выбору точки/даты) ---
@router.callback_query(TransferFSM.choosing_event, F.data == "continue_from_event_selection")
async def continue_from_event_selection(callback: CallbackQuery, state: FSMContext):
    logger.info("Нажата кнопка 'Далее' из выбора события.")
    user_data = await state.get_data()
    selected_event_id = user_data.get('selected_event_id')
    logger.debug(f"Текущий selected_event_id из состояния: '{selected_event_id}'")

    if not selected_event_id:
        await callback.answer("Пожалуйста, выберите событие, прежде чем продолжить.", show_alert=True)
        logger.warning("Пользователь нажал 'Далее' без выбранного события.")
        return

    # Получаем полное описание выбранного события для следующего шага
    event_data = get_event_data(selected_event_id)
    if not event_data:
        # Это логично, если selected_event_id есть, но get_event_data() вернул None (например, config изменился)
        logger.error(f"Данные для selected_event_id '{selected_event_id}' не найдены в конфиге при продолжении.")
        await callback.answer("Ошибка: данные о выбранном событии не найдены. Попробуйте выбрать событие заново.",
                              show_alert=True)
        # Переведем пользователя в начальное состояние выбора событий, чтобы он мог начать сначала
        await state.set_state(TransferFSM.choosing_event)
        # Также сбросим selected_event_id, чтобы не было ложной галочки
        await state.update_data(selected_event_id=None)
        return

    # Сохраняем выбранное событие (его ID и имя) в FSM контекст
    await state.update_data(event_id=selected_event_id, event_name=event_data['name'])
    logger.debug(f"Сохранено event_id: {selected_event_id}, event_name: {event_data['name']}")

    # Переходим к объединенному выбору места сдачи и даты
    try:
        await callback.message.edit_text(
            f"Отлично! Выбрано событие: <b>{event_data['name']}</b>\n"
            "Теперь выберите место и дату сдачи BikeCase:",
            reply_markup=transfer_kb.get_combined_point_date_keyboard(selected_event_id),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при получении или отправке get_combined_point_date_keyboard: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при загрузке опций. Пожалуйста, попробуйте снова.", show_alert=True)
        await state.set_state(CommonFSM.main_menu)  # Возвращаемся в главное меню при критической ошибке
        await callback.answer()
        return

    await state.set_state(TransferFSM.choosing_combined_point_date)
    await callback.answer()


# --- НОВЫЙ ОБРАБОТЧИК: выбор ОБЪЕДИНЕННОЙ кнопки Места и Даты ---
@router.callback_query(TransferFSM.choosing_combined_point_date, F.data.startswith('select_combined_dropoff_'))
async def process_combined_point_date_choice(callback: CallbackQuery, state: FSMContext):
    full_callback_data = callback.data
    logger.info(f"Обработка выбора объединенной точки/даты: {full_callback_data}")

    # Разделяем callback_data с конца, чтобы надежно получить дату и point_index
    # Например: "select_combined_dropoff_medny_vsadnik_2025_0_2025-07-07"
    # rsplit('_', 2) -> ['select_combined_dropoff_medny_vsadnik_2025', '0', '2025-07-07']
    data_parts_from_right = full_callback_data.rsplit('_', 2)

    if len(data_parts_from_right) != 3:
        logger.error(f"Некорректный формат callback_data для rsplit('_', 2): {full_callback_data}. Ожидалось 3 части.")
        await callback.answer("Ошибка: Некорректные данные для выбора. Пожалуйста, попробуйте еще раз.",
                              show_alert=True)
        return

    selected_date = data_parts_from_right[2]  # Последняя часть - дата
    point_index_str = data_parts_from_right[1]  # Вторая с конца - point_index

    try:
        point_index = int(point_index_str)
    except ValueError:
        logger.error(f"Некорректный point_index в callback_data: {point_index_str} для callback: {full_callback_data}")
        await callback.answer("Ошибка: Некорректный индекс точки. Пожалуйста, попробуйте еще раз.", show_alert=True)
        return

    # Теперь извлекаем option_type и event_id из оставшейся левой части
    # Например: 'select_combined_dropoff_medny_vsadnik_2025'
    left_part = data_parts_from_right[0]

    # Снова split, но теперь зная, что первые три части это "select", "combined", "dropoff"
    left_parts_split = left_part.split('_')
    if len(left_parts_split) < 3:  # Должно быть как минимум 'select', 'combined', 'dropoff'
        logger.error(f"Недостаточно частей в левой части callback_data: {left_part}. Ожидалось минимум 3.")
        await callback.answer("Ошибка: Некорректные данные для выбора. Пожалуйста, попробуйте еще раз.",
                              show_alert=True)
        return

    option_type = left_parts_split[2]  # 'dropoff' или 'pickup'

    # event_id - это все части после 'dropoff' и до point_index (которые мы уже отрезали)
    event_id_parts = left_parts_split[3:]
    event_id = '_'.join(event_id_parts)

    logger.debug(
        f"Извлечено: option_type={option_type}, event_id={event_id}, point_index={point_index}, selected_date={selected_date}")

    event_data = get_event_data(event_id)
    if not event_data:
        logger.error(f"Событие '{event_id}' не найдено при обработке выбора точки/даты.")
        await callback.answer("Ошибка: событие не найдено. Попробуйте выбрать событие заново.", show_alert=True)
        await state.set_state(TransferFSM.choosing_event)  # Возвращаем на выбор события
        return

    selected_point = get_option_data(event_data, option_type, point_index)
    if not selected_point:
        logger.error(f"Точка '{point_index}' типа '{option_type}' не найдена для события '{event_id}'.")
        await callback.answer("Ошибка: точка сдачи/получения не найдена.", show_alert=True)
        return

    # Сохраняем все необходимые данные для сводки заявки
    await state.update_data(
        event_id=event_id,
        current_option_type=option_type,
        selected_point_index=point_index,
        selected_point_name=selected_point['point_name'],
        selected_date=selected_date,
        selected_time=None
        # Время будем выбирать на следующем шаге, если есть несколько, или просто использовать любой слот
    )
    logger.debug(f"Сохранено в FSM: point_name='{selected_point['point_name']}', date='{selected_date}'")

    available_times = selected_point['available_slots'].get(selected_date, [])
    logger.debug(f"Доступные времена для {selected_date}: {available_times}")

    if not available_times:
        logger.warning(
            f"На дату {selected_date} нет доступных временных слотов для точки {selected_point['point_name']}.")
        await callback.answer("На выбранную дату нет доступных временных слотов. Выберите другую дату.",
                              show_alert=True)
        user_data = await state.get_data()  # Обновляем user_data после сброса
        await callback.message.edit_text(
            f"Отлично! Выбрано событие: <b>{user_data.get('event_name', 'Неизвестное событие')}</b>\n"
            "Пожалуйста, выберите место и дату сдачи BikeCase (нет слотов на выбранную дату):",
            reply_markup=transfer_kb.get_combined_point_date_keyboard(event_id),
            parse_mode="HTML"
        )
        return

    # Если есть только один временной слот, выбираем его автоматически
    if len(available_times) == 1:
        await state.update_data(selected_time=available_times[0])
        # Переходим сразу к вопросу о ремонте
        user_data = await state.get_data()
        text_message = (
            f"Выбраны: <b>{selected_point['point_name']}</b>, <b>{selected_date}</b>, <b>{available_times[0]}</b>.\n\n"
            "Нужен ли BikeCase предв. ремонт или сборка/разборка? "
            "Нажмите 'Нет, не требуется' или оставьте комментарий для механика. Например, 'ТО' или 'проверить всё'."
        )
        await callback.message.edit_text(
            text_message,
            reply_markup=transfer_kb.get_repair_keyboard(),  # Клавиатура с "Нет, не требуется"
            parse_mode="HTML"
        )
        await state.set_state(TransferFSM.asking_for_repair)
    else:
        # Если есть несколько слотов, предлагаем выбрать время (это можно будет реализовать позже, если потребуется)
        # Пока что, если слотов несколько, мы просто берем первый
        await state.update_data(selected_time=available_times[0])  # TODO: Реализовать выбор времени, если это нужно

        user_data = await state.get_data()
        text_message = (
            f"Выбраны: <b>{selected_point['point_name']}</b>, <b>{selected_date}</b>.\n"
            f"Доступные времена: {', '.join(available_times)}. Выбрано: <b>{available_times[0]}</b>.\n\n"  # TODO: Убрать "Выбрано", если реализуется выбор
            "Нужен ли BikeCase предв. ремонт или сборка/разборка? "
            "Нажмите 'Нет, не требуется' или оставьте комментарий для механика. Например, 'ТО' или 'проверить всё'."
        )
        await callback.message.edit_text(
            text_message,
            reply_markup=transfer_kb.get_repair_keyboard(),
            parse_mode="HTML"
        )
        await state.set_state(TransferFSM.asking_for_repair)

    await callback.answer()


# --- ОБРАБОТЧИК: "Нет, не требуется" (для ремонта) ---
@router.callback_query(TransferFSM.asking_for_repair, F.data == "repair_no_required")
async def process_repair_no_required(callback: CallbackQuery, state: FSMContext):
    logger.info("Ремонт не требуется. Переход к сводке.")
    await state.update_data(pre_repair=False, pre_repair_comment=None)
    user_data = await state.get_data()
    user_db_data = await db_stubs.get_user(callback.from_user.id)
    is_user_registered = user_db_data and all(user_db_data.get(field) for field in [
        'full_name', 'phone_number', 'passport_series_number', 'passport_issued_by',
        'passport_date_of_issue', 'registration_address'
    ])

    summary = format_application_summary(user_data)  # Передаем только user_data

    await callback.message.edit_text(
        f"Предварительный ремонт не требуется.\n\n"
        f"Ваша заявка готова. Проверьте данные:\n\n{summary}\n\n"
        "Что будем делать дальше?",
        reply_markup=transfer_kb.get_confirmation_keyboard(is_user_registered=is_user_registered),
        parse_mode="HTML"
    )
    await state.set_state(TransferFSM.final_summary)
    await callback.answer()


# --- НОВЫЙ ОБРАБОТЧИК: Ввод комментария для механика (в состоянии TransferFSM.asking_for_repair) ---
# Теперь F.text в этом состоянии обрабатывается как сам комментарий.
@router.message(TransferFSM.asking_for_repair, F.text)
async def process_pre_repair_comment_directly(message: Message, state: FSMContext):
    comment = message.text
    logger.info(f"Получен комментарий к ремонту (напрямую из asking_for_repair): '{comment[:50]}...'")
    if not comment or not comment.strip():  # Проверяем только на пустоту
        await message.reply(
            "Комментарий не может быть пустым. Пожалуйста, опишите, какой ремонт или сборка/разборка вам требуется. Например, 'ТО' или 'проверить всё':")
        return

    await state.update_data(pre_repair=True, pre_repair_comment=comment)  # Сохраняем, что ремонт нужен и комментарий
    user_data = await state.get_data()
    user_db_data = await db_stubs.get_user(message.from_user.id)
    is_user_registered = user_db_data and all(user_db_data.get(field) for field in [
        'full_name', 'phone_number', 'passport_series_number', 'passport_issued_by',
        'passport_date_of_issue', 'registration_address'
    ])

    summary = format_application_summary(user_data)  # Передаем только user_data

    await message.answer(  # Использовать answer, так как это сообщение от пользователя, а не редактирование
        f"Комментарий к ремонту сохранен.\n\n"
        f"Ваша заявка готова. Проверьте данные:\n\n{summary}\n\n"
        "Что будем делать дальше?",
        reply_markup=transfer_kb.get_confirmation_keyboard(is_user_registered=is_user_registered),
        parse_mode="HTML"
    )
    await state.set_state(TransferFSM.final_summary)


# --- ОБРАБОТЧИКИ НАЗАД ---

# Возврат к выбору объединенной точки/даты из вопроса о ремонте
@router.callback_query(TransferFSM.asking_for_repair, F.data == "back_to_choosing_combined_point_date")
async def back_to_choosing_combined_point_date_from_repair(callback: CallbackQuery, state: FSMContext):
    logger.info(
        f"Нажата кнопка 'Назад' из вопроса о ремонте. Текущее состояние: {await state.get_state()}. Callback data: {callback.data}")
    user_data = await state.get_data()
    event_id = user_data.get('event_id')
    event_name = user_data.get('event_name', 'Неизвестное событие')

    if not event_id:
        logger.error("Ошибка при возврате из ремонта: событие не выбрано в состоянии.")
        await callback.answer("Ошибка при возврате: событие не выбрано. Пожалуйста, попробуйте начать заново.",
                              show_alert=True)
        await state.set_state(CommonFSM.main_menu)  # При критической ошибке возвращаем в главное меню
        return

    # Сброс данных, относящихся к ремонту, чтобы при повторном входе в этот шаг они были чистыми
    await state.update_data(pre_repair=None, pre_repair_comment=None)

    await callback.message.edit_text(
        f"Вернулись к выбору места и даты сдачи BikeCase для события: <b>{event_name}</b>:",
        reply_markup=transfer_kb.get_combined_point_date_keyboard(event_id),
        parse_mode="HTML"
    )
    await state.set_state(TransferFSM.choosing_combined_point_date)
    await callback.answer()


# Возврат к выбору события из выбора точки сдачи (КОЛЛБЭК ИЗ ОБЪЕДИНЕННОЙ КЛАВИАТУРЫ)
@router.callback_query(TransferFSM.choosing_combined_point_date, F.data == "back_to_choosing_event")
async def back_to_choosing_event_from_combined_point_date(callback: CallbackQuery, state: FSMContext):
    logger.info(
        f"Нажата кнопка 'Назад' из выбора места/даты. Текущее состояние: {await state.get_state()}. Callback data: {callback.data}")
    user_data = await state.get_data()
    selected_event_id = user_data.get('event_id')  # Используем 'event_id', который уже сохранен

    # Сбрасываем данные о точке, дате, времени, типе, если они были
    await state.update_data(current_option_type=None, selected_point_index=None, selected_point_name=None,
                            selected_date=None, selected_time=None)

    event_description = "Выберите событие из списка ниже, чтобы увидеть его описание."
    if selected_event_id:
        event_data = get_event_data(selected_event_id)
        if event_data:
            event_description = event_data.get('description', event_description)
    else:
        logger.warning("selected_event_id не найден при возврате к выбору события. Устанавливаем в None.")
        selected_event_id = None  # Обеспечиваем, что selected_event_id будет None, если он почему-то потерялся

    await callback.message.edit_text(
        event_description,
        reply_markup=transfer_kb.get_events_keyboard(selected_event_id=selected_event_id),
        # Передаем selected_event_id для галочки
        parse_mode="HTML"
    )
    await state.set_state(TransferFSM.choosing_event)
    await callback.answer()


# Возврат в Главное меню из выбора событий трансфера
@router.callback_query(TransferFSM.choosing_event, F.data == "back_to_main_menu_from_transfer_event_selection")
async def back_to_main_menu_from_transfer_event_selection(callback: CallbackQuery, state: FSMContext):
    logger.info(
        f"Нажата кнопка '⬅️ Назад' из выбора событий трансфера. Текущее состояние: {await state.get_state()}. Callback data: {callback.data}")

    user_data = await db_stubs.get_user(callback.from_user.id)  # Получаем данные пользователя
    # Проверка, зарегистрирован ли пользователь полностью для корректного приветствия
    is_fully_registered = user_data and all(user_data.get(field) for field in [
        'full_name', 'phone_number', 'passport_series_number', 'passport_issued_by',
        'passport_date_of_issue', 'registration_address'
    ])
    text = f"С возвращением, {hbold(user_data['full_name'])}! Выберите действие:" if is_fully_registered else "Здравствуйте! Это бот для оформления заявок на трансфер велосипедов. Выберите действие:"

    await state.update_data(selected_event_id=None)  # Сбрасываем выбранное событие
    try:
        await callback.message.edit_text(
            text,
            reply_markup=common_kb.get_main_menu_keyboard(),  # Возвращаемся к общей клавиатуре главного меню
            parse_mode="HTML"
        )
    except TelegramBadRequest as e:
        logger.warning(f"TelegramBadRequest при возврате в главное меню: {e}. Возможно, сообщение не изменилось.")
        # Это может быть, если пользователь быстро нажимает "Назад" несколько раз.
        # Просто отвечаем на коллбэк, чтобы избежать спама ошибками.
        pass

    await state.set_state(CommonFSM.main_menu)  # Переходим в состояние главного меню
    logger.info(f"Переход в состояние: {await state.get_state()}")
    await callback.answer()


# Возврат к вопросу о ремонте из финальной сводки
@router.callback_query(TransferFSM.final_summary, F.data == "back_to_repair_question")
async def back_to_repair_question_from_summary(callback: CallbackQuery, state: FSMContext):
    logger.info(
        f"Нажата кнопка 'Назад' из финальной сводки. Текущее состояние: {await state.get_state()}. Callback data: {callback.data}")
    # При возврате из сводки, всегда показываем единый экран с вопросом о ремонте
    await state.update_data(pre_repair=None,
                            pre_repair_comment=None)  # Сброс, чтобы начать с чистого листа при возврате

    await callback.message.edit_text(
        "Нужен ли BikeCase предв. ремонт или сборка/разборка? "
        "Нажмите 'Нет, не требуется' или оставьте комментарий для механика. Например, 'ТО' или 'проверить всё'.",
        reply_markup=transfer_kb.get_repair_keyboard(),
        parse_mode="HTML"
    )
    await state.set_state(TransferFSM.asking_for_repair)
    await callback.answer()


# --- ОБРАБОТЧИКИ ФИНАЛЬНОГО ЭТАПА ---

# Переименовал функцию в confirm_application, чтобы она была доступна для импорта из registration/handlers.py
# Она должна уметь принимать как CallbackQuery, так и Message
@router.callback_query(TransferFSM.final_summary, F.data == "confirm_application")
@router.message(TransferFSM.final_summary, Command("confirm"))  # Если вдруг будет нужна команда для подтверждения
async def confirm_application(update: Message | CallbackQuery, state: FSMContext):
    logger.info("Подтверждение заявки.")
    user_id = update.from_user.id
    user_data = await state.get_data()

    # Здесь должна быть логика сохранения заявки в БД и генерации договора
    application_id = await db_stubs.create_application(user_id, user_data)  # Имитация сохранения
    # TODO: Добавить логику генерации Word-договора и отправки его в чат
    # Пока просто сообщение о завершении

    text_to_send = (
        "✅ Ваша заявка успешно оформлена!\n"
        f"Номер вашей заявки: <b>#{application_id}</b>\n"
        "В ближайшее время с вами свяжется менеджер BikeCase для уточнения деталей.\n\n"
        "Договор будет сформирован и отправлен вам в чат (функция находится в разработке)."
    )

    if isinstance(update, CallbackQuery):
        await update.message.edit_text(
            text_to_send,
            parse_mode="HTML",
            reply_markup=common_kb.get_main_menu_keyboard()  # Возвращаем в главное меню
        )
        await update.answer()
    else:  # Если это Message
        await update.answer(
            text_to_send,
            parse_mode="HTML",
            reply_markup=common_kb.get_main_menu_keyboard()  # Возвращаем в главное меню
        )

    await state.clear()
    await state.set_state(CommonFSM.main_menu)  # Возвращаемся в главное меню


# Отдельная функция для показа сводки, которая может быть вызвана из разных мест
# Принимает либо CallbackQuery, либо Message
async def show_final_summary(update: Message | CallbackQuery, state: FSMContext):
    logger.info(f"Отображение финальной сводки для пользователя {update.from_user.id}.")
    user_data = await state.get_data()
    user_db_data = await db_stubs.get_user(update.from_user.id)
    is_user_registered = user_db_data and all(user_db_data.get(field) for field in [
        'full_name', 'phone_number', 'passport_series_number', 'passport_issued_by',
        'passport_date_of_issue', 'registration_address'
    ])

    summary = format_application_summary(user_data)

    text_message = (
        f"Ваша заявка готова. Проверьте данные:\n\n{summary}\n\n"
        "Что будем делать дальше?"
    )

    if isinstance(update, CallbackQuery):
        try:
            await update.message.edit_text(
                text_message,
                reply_markup=transfer_kb.get_confirmation_keyboard(is_user_registered=is_user_registered),
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            logger.warning(f"TelegramBadRequest при редактировании сводки: {e}. Отправляем новое сообщение.")
            await update.message.answer(
                text_message,
                reply_markup=transfer_kb.get_confirmation_keyboard(is_user_registered=is_user_registered),
                parse_mode="HTML"
            )
        await update.answer()
    else:  # Если это Message
        await update.answer(
            text_message,
            reply_markup=transfer_kb.get_confirmation_keyboard(is_user_registered=is_user_registered),
            parse_mode="HTML"
        )
    await state.set_state(TransferFSM.final_summary)


# ОБРАБОТЧИК: Отмена заявки из финальной сводки
@router.callback_query(TransferFSM.final_summary, F.data == "cancel_application")
async def cancel_application(callback: CallbackQuery, state: FSMContext):
    logger.info("Отмена заявки.")
    await state.clear()
    await callback.message.edit_text(
        "❌ Оформление заявки отменено. Вы можете начать заново из главного меню.",
        reply_markup=common_kb.get_main_menu_keyboard()
    )
    await state.set_state(CommonFSM.main_menu)
    await callback.answer()


# ОБРАБОТЧИК: Запуск регистрации из финальной сводки (если пользователь не зарегистрирован)
@router.callback_query(TransferFSM.final_summary, F.data == "start_registration_from_summary")
async def start_registration_from_summary(callback: CallbackQuery, state: FSMContext):
    logger.info("Начало регистрации из сводки заявки.")
    # Сохраняем данные заявки временно, чтобы после регистрации можно было вернуться и подтвердить
    user_data = await state.get_data()
    await state.set_data(user_data)  # Сохраняем текущие данные заявки
    await state.update_data(return_to_transfer_summary=True)  # Флаг для возврата

    await callback.message.edit_text(
        "Для оформления заявки вам необходимо зарегистрироваться.\n"
        "Пожалуйста, введите ваше полное имя (Фамилия Имя Отчество):",
        reply_markup=registration_kb.get_registration_start_keyboard(add_back_button=True),
        # Добавим кнопку назад для регистрации
        parse_mode="HTML"
    )
    await state.set_state(RegistrationFSM.entering_full_name)  # Переходим в FSM регистрации
    await callback.answer()
