from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters import IsGroup
from database import update_chat_setting, get_chat_settings
from utils import is_admin
from handlers.commands import get_command, extract_args

router = Router()
router.message.filter(IsGroup())

@router.message(F.text)
async def handle_admin_commands(message: Message):
    cmd = get_command(message.text)
    if not cmd:
        return
    
    args = extract_args(message.text)
    
    if cmd == "admins":
        await cmd_admins(message)
    elif cmd == "settings":
        await cmd_settings(message)
    elif cmd == "set_welcome":
        await cmd_set_welcome(message, CommandObject(args=args))
    elif cmd == "set_antiflood":
        await cmd_set_antiflood(message, CommandObject(args=args))
    elif cmd == "set_mute":
        await cmd_set_mute(message, CommandObject(args=args))
    elif cmd == "set_ban":
        await cmd_set_ban(message, CommandObject(args=args))

@router.message(Command("admins"))
async def cmd_admins(message: Message):
    try:
        admins = await message.bot.get_chat_administrators(message.chat.id)
        lines = []
        for admin in admins:
            user = admin.user
            if user.username:
                name = f"@{user.username}"
            else:
                name = user.full_name
            lines.append(f"• {name}" + (" (создатель)" if admin.status == "creator" else ""))
        await message.answer("👮‍♂️ <b>Администраторы чата:</b>\n" + "\n".join(lines))
    except Exception as e:
        await message.answer("❌ Не удалось получить список администраторов.")

@router.message(Command("settings"))
async def cmd_settings(message: Message):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    settings = await get_chat_settings(message.chat.id)
    welcome, antiflood, mute_dur, ban_dur = settings
    
    text = (
        "⚙️ <b>Настройки чата:</b>\n"
        f"Приветствие: {'✅' if welcome else '❌'}\n"
        f"Антифлуд: {'✅' if antiflood else '❌'}\n"
        f"Длительность мута: {mute_dur} сек.\n"
        f"Длительность бана: {ban_dur} сек.\n\n"
        "Для изменения:\n"
        "/set_welcome on/off  или  приветствие on/off\n"
        "/set_antiflood on/off  или  антифлуд on/off\n"
        "/set_mute <сек>  или  мут время <сек>\n"
        "/set_ban <сек>  или  бан время <сек>"
    )
    await message.answer(text)

@router.message(Command("set_welcome"))
async def cmd_set_welcome(message: Message, command: CommandObject):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not command.args:
        await message.reply("Укажите on или off")
        return
    
    value = command.args.lower()
    if value == "on":
        await update_chat_setting(message.chat.id, "welcome_enabled", 1)
        await message.reply("✅ Приветствие включено")
    elif value == "off":
        await update_chat_setting(message.chat.id, "welcome_enabled", 0)
        await message.reply("✅ Приветствие выключено")
    else:
        await message.reply("Используйте: /set_welcome on/off  или  приветствие on/off")

@router.message(Command("set_antiflood"))
async def cmd_set_antiflood(message: Message, command: CommandObject):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not command.args:
        await message.reply("Укажите on или off")
        return
    
    value = command.args.lower()
    if value == "on":
        await update_chat_setting(message.chat.id, "antiflood_enabled", 1)
        await message.reply("✅ Антифлуд включен")
    elif value == "off":
        await update_chat_setting(message.chat.id, "antiflood_enabled", 0)
        await message.reply("✅ Антифлуд выключен")
    else:
        await message.reply("Используйте: /set_antiflood on/off  или  антифлуд on/off")

@router.message(Command("set_mute"))
async def cmd_set_mute(message: Message, command: CommandObject):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not command.args:
        await message.reply("Укажите длительность в секундах")
        return
    
    try:
        duration = int(command.args.split()[0])
        if duration <= 0:
            raise ValueError
        await update_chat_setting(message.chat.id, "mute_duration", duration)
        await message.reply(f"✅ Длительность мута установлена: {duration} сек.")
    except:
        await message.reply("Укажите положительное число")

@router.message(Command("set_ban"))
async def cmd_set_ban(message: Message, command: CommandObject):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    if not command.args:
        await message.reply("Укажите длительность в секундах")
        return
    
    try:
        duration = int(command.args.split()[0])
        if duration <= 0:
            raise ValueError
        await update_chat_setting(message.chat.id, "ban_duration", duration)
        await message.reply(f"✅ Длительность бана установлена: {duration} сек.")
    except:
        await message.reply("Укажите положительное число")