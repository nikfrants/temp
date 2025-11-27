from aiogram.fsm.state import State, StatesGroup

class TransferFSM(StatesGroup):
    choosing_event = State()                    # Выбор события
    choosing_combined_point_date = State()      # Выбор места и даты сдачи/получения (объединенный шаг)
    asking_for_repair = State()                 # Вопрос о необходимости ремонта (теперь включает ввод комментария)
    entering_repair_comment = State()           # Ожидание ввода комментария к ремонту
    final_summary = State()                     # Итоговая информация и подтверждение
    # ... другие состояния, специфичные для флоу трансфера
