"""
Модуль автоматического определения одиночного слова "Да".

Если пользователь отправляет сообщение, состоящее исключительно из слова
"да" (в любом регистре, кириллица или латиница), бот автоматически отвечает.
Триггер срабатывает только на полностью совпадающее слово, например:
- "да", "ДА", "Да" — срабатывает → ответ "Пизда"
- "da", "DA", "Da" — срабатывает → ответ "Pizda"
- "Да!", "ДА!", "DA!" — срабатывает (после удаления пунктуации)
- "Да, наверное" — не срабатывает
- "Дача" — не срабатывает
- "может да" — не срабатывает

Защита от дублирования: бот отвечает на каждое уникальное сообщение "Да"
ровно один раз (по message_id). На каждое новое "Да" — отвечает снова.
"""
import logging
import re
import time
from typing import Tuple

logger = logging.getLogger(__name__)

# Хранение ID сообщений, на которые уже был дан ответ
_processed_message_ids: dict = {}

# Время жизни записи (1 минута — больше чем достаточно)
MAX_AGE_SECONDS = 60


def check_single_da_message(text: str, message_id: int = None) -> Tuple[bool, str]:
    """
    Проверяет, является ли сообщение одиночным словом "да" / "da".

    Args:
        text: Текст сообщения пользователя.
        message_id: ID сообщения ВКонтакте (для защиты от повторных ответов).

    Returns:
        Кортеж (is_match, response), где:
        - is_match: True, если сообщение — одиночное "да"/"da" и ещё не отвечали
        - response: ответ бота ("Пизда" или "Pizda")
    """
    # Очищаем старые записи
    _cleanup_old_entries()

    # Если message_id уже обработан — не отвечаем повторно
    if message_id is not None and message_id in _processed_message_ids:
        logger.info(f"🪗 Сообщение {message_id} уже обработано, пропускаем")
        return False, ""

    # Удаляем все символы пунктуации и пробелы по краям
    cleaned = text.strip()
    cleaned = re.sub(r'[^\w\s]', '', cleaned, flags=re.UNICODE)
    cleaned = cleaned.strip()

    # Разбиваем на слова
    words = cleaned.split()

    # Должно быть ровно одно слово
    if len(words) != 1:
        return False, ""

    word_lower = words[0].lower()

    if word_lower not in ('да', 'da'):
        return False, ""

    # Запоминаем ID сообщения
    if message_id is not None:
        _processed_message_ids[message_id] = time.time()

    if word_lower == 'да':
        logger.info(f"🪗 Обнаружено одиночное 'да' (msg_id={message_id})")
        return True, "Пизда"
    elif word_lower == 'da':
        logger.info(f"🪗 Обнаружено одиночное 'da' (msg_id={message_id})")
        return True, "Pizda"

    return False, ""


def _cleanup_old_entries():
    """Удаляет записи старше MAX_AGE_SECONDS"""
    current_time = time.time()
    expired = [
        msg_id for msg_id, ts in _processed_message_ids.items()
        if current_time - ts > MAX_AGE_SECONDS
    ]
    for msg_id in expired:
        del _processed_message_ids[msg_id]