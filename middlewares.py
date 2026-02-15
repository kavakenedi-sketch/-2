import asyncio
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message
from database import get_chat_settings

logger = logging.getLogger(__name__)

class AntifloodMiddleware(BaseMiddleware):
    def __init__(self, default_delay: int = 2):
        self.default_delay = default_delay
        self.user_last_message = {}

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        if not event.text or event.chat.type not in ("group", "supergroup"):
            return await handler(event, data)

        settings = await get_chat_settings(event.chat.id)
        if not settings[1]:
            return await handler(event, data)

        key = (event.chat.id, event.from_user.id)
        now = asyncio.get_event_loop().time()
        last = self.user_last_message.get(key, 0)
        if now - last < self.default_delay:
            return
        self.user_last_message[key] = now
        return await handler(event, data)

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        logger.info(f"Получено сообщение от {event.from_user.id} в чате {event.chat.id}: {event.text}")
        return await handler(event, data)