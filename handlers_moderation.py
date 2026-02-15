from aiogram import Router, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from filters import IsGroup
from database import add_warn, remove_warn, log_moderation, get_chat_settings
from utils import is_admin
import datetime
from config import Config
from handlers.commands import get_command, extract_args

router = Router()
router.message.filter(IsGroup())
config = Config()

@router.message(F.text)
async def handle_moderation_commands(message: Message):
    cmd = get_command(message.text)
    if not cmd:
        return
    
    args = extract_args(message.text)
    
    if cmd == "mute":
        await cmd_mute(message, CommandObject(args=args))
    elif cmd == "unmute":
        await cmd_unmute(message)
    elif cmd == "kick":
        await cmd_kick(message)
    elif cmd == "ban":
        await cmd_ban(message, CommandObject(args=args))
    elif cmd == "unban":
        await cmd_unban(message)
    elif cmd == "warn":
        await cmd_warn(message, CommandObject(args=args))
    elif cmd == "unwarn":
        await cmd_unwarn(message)

@router.message(Command("mute"))
async def cmd_mute(message: Message, command: CommandObject):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        await message.reply("❌ Эта команда только для администраторов.")
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Ответьте на сообщение пользователя, которого хотите замутить.")
        return
    
    target = message.reply_to_message.from_user
    if target.id == message.bot.id:
        await message.reply("❌ Не могу замутить самого себя.")
        return
    
    if await is_admin(message.bot, message.chat.id, target.id):
        await message.reply("❌ Нельзя замутить администратора.")
        return

    settings = await get_chat_settings(message.chat.id)
    mute_duration = settings[2]
    
    until_date = datetime.datetime.now() + datetime.timedelta(seconds=mute_duration)
    permissions = ChatPermissions(can_send_messages=False)
    
    try:
        await message.bot.restrict_chat_member(
            message.chat.id, target.id, permissions, until_date=until_date
        )
        await message.reply(f"🔇 Пользователь {target.full_name} замучен на {mute_duration} секунд.")
        await log_moderation(message.chat.id, message.from_user.id, "mute", target.id)
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@router.message(Command("unmute"))
async def cmd_unmute(message: Message):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Ответьте на сообщение пользователя.")
        return
    
    target = message.reply_to_message.from_user
    permissions = ChatPermissions(can_send_messages=True)
    
    try:
        await message.bot.restrict_chat_member(message.chat.id, target.id, permissions)
        await message.reply(f"🔊 Пользователь {target.full_name} размучен.")
        await log_moderation(message.chat.id, message.from_user.id, "unmute", target.id)
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@router.message(Command("kick"))
async def cmd_kick(message: Message):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Ответьте на сообщение.")
        return
    
    target = message.reply_to_message.from_user
    if await is_admin(message.bot, message.chat.id, target.id):
        await message.reply("❌ Нельзя кикнуть администратора.")
        return
    
    try:
        await message.bot.ban_chat_member(message.chat.id, target.id)
        await message.bot.unban_chat_member(message.chat.id, target.id)
        await message.reply(f"👢 Пользователь {target.full_name} кикнут.")
        await log_moderation(message.chat.id, message.from_user.id, "kick", target.id)
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@router.message(Command("ban"))
async def cmd_ban(message: Message, command: CommandObject):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Ответьте на сообщение.")
        return
    
    target = message.reply_to_message.from_user
    if await is_admin(message.bot, message.chat.id, target.id):
        await message.reply("❌ Нельзя забанить администратора.")
        return
    
    settings = await get_chat_settings(message.chat.id)
    ban_duration = settings[3]
    until_date = datetime.datetime.now() + datetime.timedelta(seconds=ban_duration)
    
    try:
        await message.bot.ban_chat_member(message.chat.id, target.id, until_date=until_date)
        await message.reply(f"🔨 Пользователь {target.full_name} забанен на {ban_duration} секунд.")
        await log_moderation(message.chat.id, message.from_user.id, "ban", target.id)
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@router.message(Command("unban"))
async def cmd_unban(message: Message):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Ответьте на сообщение.")
        return
    
    target = message.reply_to_message.from_user
    
    try:
        await message.bot.unban_chat_member(message.chat.id, target.id)
        await message.reply(f"✅ Пользователь {target.full_name} разбанен.")
        await log_moderation(message.chat.id, message.from_user.id, "unban", target.id)
    except Exception as e:
        await message.reply(f"❌ Ошибка: {e}")

@router.message(Command("warn"))
async def cmd_warn(message: Message, command: CommandObject):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Ответьте на сообщение.")
        return
    
    target = message.reply_to_message.from_user
    if await is_admin(message.bot, message.chat.id, target.id):
        await message.reply("❌ Нельзя выдать предупреждение администратору.")
        return
    
    reason = command.args or "Не указана"
    warns = await add_warn(message.chat.id, target.id)
    await message.reply(f"⚠️ {target.full_name} получил предупреждение ({warns}/{config.MAX_WARNS}).\nПричина: {reason}")
    await log_moderation(message.chat.id, message.from_user.id, "warn", target.id, reason)

    if warns >= config.MAX_WARNS:
        settings = await get_chat_settings(message.chat.id)
        mute_duration = settings[2]
        until_date = datetime.datetime.now() + datetime.timedelta(seconds=mute_duration)
        permissions = ChatPermissions(can_send_messages=False)
        try:
            await message.bot.restrict_chat_member(
                message.chat.id, target.id, permissions, until_date=until_date
            )
            await message.answer(
                f"🔇 {target.full_name} получил {warns} предупреждений "
                f"и был замучен на {mute_duration} секунд."
            )
        except:
            pass

@router.message(Command("unwarn"))
async def cmd_unwarn(message: Message):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Ответьте на сообщение.")
        return
    
    target = message.reply_to_message.from_user
    warns = await remove_warn(message.chat.id, target.id)
    await message.reply(f"✅ У {target.full_name} снято предупреждение. Текущее количество: {warns}")
    await log_moderation(message.chat.id, message.from_user.id, "unwarn", target.id)