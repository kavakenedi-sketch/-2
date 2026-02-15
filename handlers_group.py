from aiogram import Router, F
from aiogram.types import Message
from filters import IsGroup
from database import update_user_info, add_message, get_chat_settings, update_hidden_rank
from handlers.commands import get_command
import logging

router = Router()
router.message.filter(IsGroup())

@router.message(F.text)
async def handle_message(message: Message):
    cmd = get_command(message.text)
    if cmd:
        return
    
    await update_user_info(
        message.from_user.id,
        message.from_user.username,
        message.from_user.first_name,
        message.from_user.last_name
    )
    
    await add_message(message.chat.id, message.from_user.id, message.text)
    
    new_rank = await update_hidden_rank(message.chat.id, message.from_user.id)
    if new_rank:
        logging.info(f"Пользователь {message.from_user.id} получил скрытый ранг {new_rank}")

@router.message(F.new_chat_members)
async def welcome_new_member(message: Message):
    settings = await get_chat_settings(message.chat.id)
    if settings[0]:
        for user in message.new_chat_members:
            if user.id == message.bot.id:
                continue
            await message.answer(
                f"👋 Добро пожаловать, {user.full_name}!\n"
                "Здесь мы собираем статистику и ценим грамотное общение."
            )