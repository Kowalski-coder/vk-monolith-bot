"""
Клиент для работы с API Гигачата
"""
import aiohttp
import uuid
from typing import List, Dict, Optional
from config import GIGACHAT_AUTH_KEY, GIGACHAT_SCOPE, SYSTEM_PROMPT, MAX_TOKENS
from history import history_manager


class GigaChatClient:
    """Клиент для отправки запросов в Гигачат"""

    def __init__(self):
        self.auth_url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
        self.api_base_url = "https://gigachat.devices.sberbank.ru/api/v1"
        self.model = "GigaChat"
        self.auth_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
            'RqUID': str(uuid.uuid4()),
            'Authorization': f'Basic {GIGACHAT_AUTH_KEY}'
        }
        self.auth_payload = {
            'scope': GIGACHAT_SCOPE
        }
        self.access_token = None
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Возвращает переиспользуемую сессию (создаёт при первом вызове)"""
        if self._session is None or self._session.closed:
            connector = aiohttp.TCPConnector(ssl=False)
            self._session = aiohttp.ClientSession(connector=connector)
        return self._session

    async def close(self):
        """Закрытие сессии при остановке бота"""
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get_access_token(self) -> bool:
        """Получение Access Token через OAuth"""
        try:
            session = await self._get_session()
            async with session.post(
                self.auth_url,
                headers=self.auth_headers,
                data=self.auth_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data.get('access_token')
                    if self.access_token:
                        return True
                else:
                    return False
        except Exception:
            return False
        return False

    async def chat_with_personalized_prompt(self, user_message: str, chat_id: str, personalized_prompt: str) -> str:
        """
        Отправка сообщения в Гигачат с персонализированным промптом.
        История берётся из history_manager (единый источник).

        Args:
            user_message: Сообщение пользователя
            chat_id: ID беседы/пользователя
            personalized_prompt: Персонализированный промпт для пользователя

        Returns:
            Ответ от Гигачата
        """
        # Проверяем наличие Access Token
        if not self.access_token:
            if not await self._get_access_token():
                return "Мои механизмы сейчас не отвечают... Попробуй позже."

        # Берём историю из history_manager (уже включает сообщение пользователя,
        # сохранённое bot.py до вызова этого метода)
        history = history_manager.get_messages_for_gigachat(chat_id)

        # Формируем список сообщений: системный промпт + история
        messages = [{"role": "system", "content": personalized_prompt}]
        messages.extend(history)

        api_headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            session = await self._get_session()
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": MAX_TOKENS
            }

            async with session.post(
                f"{self.api_base_url}/chat/completions",
                headers=api_headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    assistant_message = data["choices"][0]["message"]["content"]
                    return assistant_message
                else:
                    # Попробуем получить новый токен
                    if response.status == 401:
                        self.access_token = None
                        if await self._get_access_token():
                            return await self.chat_with_personalized_prompt(user_message, chat_id, personalized_prompt)
                    return "Механизмы пока молчат... Попробуй позже."

        except Exception:
            return "Что-то сломалось в моих механизмах... Попробуй позже."

    async def test_connection(self) -> bool:
        """Тестирование подключения к GigaChat API"""
        if not self.access_token:
            if not await self._get_access_token():
                return False

        api_headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.access_token}'
        }

        try:
            session = await self._get_session()
            async with session.get(
                f"{self.api_base_url}/models",
                headers=api_headers
            ) as response:
                if response.status == 200:
                    print("Подключение к GigaChat API успешно!")
                    return True
                else:
                    error_text = await response.text()
                    print(f"Ошибка подключения к GigaChat API: {response.status}, {error_text}")
                    return False
        except Exception as e:
            print(f"Ошибка при тестировании подключения: {e}")
            return False


# Глобальный экземпляр клиента
gigachat_client = GigaChatClient()
