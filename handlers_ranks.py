from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters import IsGroup
from database import set_custom_rank
from utils import is_creator, is_admin, ADMIN_RANKS
from handlers.commands import get_command, extract_args

router = Router()
router.message.filter(IsGroup())

@router.message(F.text)
async def handle_rank_commands(message: Message):
    cmd = get_command(message.text)
    if not cmd:
        return
    
    args = extract_args(message.text)
    
    if cmd == "setrank":
        await cmd_setrank(message, CommandObject(args=args))
    elif cmd == "adminranks":
        await cmd_admin_ranks(message)
    elif cmd == "hiddenrank":
        await cmd_hidden_rank(message)

@router.message(Command("setrank"))
async def cmd_setrank(message: Message, command: CommandObject):
    if not await is_creator(message.bot, message.chat.id, message.from_user.id):
        await message.reply("❌ Только владелец чата может назначать админ-ранги.")
        return
    
    if not message.reply_to_message:
        await message.reply("❌ Ответьте на сообщение пользователя.")
        return
    
    if not command.args:
        await message.reply("❌ Укажите номер ранга (1-6) или 0 для сброса.")
        return
    
    try:
        rank = int(command.args.split()[0])
        if rank < 0 or rank > 6:
            raise ValueError
    except:
        await message.reply("❌ Номер ранга должен быть от 0 до 6 (0 - сбросить админ-ранг).")
        return
    
    target = message.reply_to_message.from_user
    
    if rank == 0:
        await set_custom_rank(message.chat.id, target.id, None)
        await message.reply(f"✅ У пользователя {target.full_name} сброшен админ-ранг.")
    else:
        await set_custom_rank(message.chat.id, target.id, rank)
        rank_name = ADMIN_RANKS[rank - 1]
        await message.reply(f"👑 Пользователю {target.full_name} назначен админ-ранг «{rank_name}».")

@router.message(Command("adminranks"))
async def cmd_admin_ranks(message: Message):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    ranks_info = [
        "1. Смотрящий",
        "2. Надзиратель",
        "3. Хранитель",
        "4. Страж",
        "5. Правитель",
        "6. Властелин"
    ]
    text = "👑 <b>Административные ранги:</b>\n" + "\n".join(ranks_info)
    await message.answer(text)

@router.message(Command("hiddenrank"))
async def cmd_hidden_rank(message: Message):
    from handlers.stats import cmd_hidden_rank as stats_hidden_rank
    await stats_hidden_rank(message)