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
"""
import logging
import re
from typing import Tuple

logger = logging.getLogger(__name__)


def check_single_da_message(text: str) -> Tuple[bool, str]:
    """
    Проверяет, является ли сообщение одиночным словом "да" / "da".

    Args:
        text: Текст сообщения пользователя.

    Returns:
        Кортеж (is_match, response), где:
        - is_match: True, если сообщение — одиночное "да"/"da"
        - response: ответ бота ("Пизда" или "Pizda")
    """
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

    if word_lower == 'да':
        logger.info(f"🪗 Обнаружено одиночное 'да' от пользователя")
        return True, "Пизда"
    elif word_lower == 'da':
        logger.info(f"🪗 Обнаружено одиночное 'da' от пользователя")
        return True, "Pizda"

    return False, ""
