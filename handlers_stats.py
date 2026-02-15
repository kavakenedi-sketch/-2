from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from filters import IsGroup
from database import get_top, get_user_stats
from utils import get_username_or_name, get_display_rank, format_number, is_admin
import aiosqlite
from database import DB_PATH
from handlers.commands import get_command, extract_args

router = Router()
router.message.filter(IsGroup())

@router.message(F.text)
async def handle_commands(message: Message):
    cmd = get_command(message.text)
    if not cmd:
        return
    
    args = extract_args(message.text)
    
    if cmd == "top":
        await cmd_top(message)
    elif cmd == "mystats":
        await cmd_mystats(message)
    elif cmd == "rank":
        await cmd_rank(message)

@router.message(Command("top"))
async def cmd_top(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="За день", callback_data="top_day")
    builder.button(text="За неделю", callback_data="top_week")
    builder.button(text="За всё время", callback_data="top_all")
    builder.adjust(3)
    await message.answer("🏆 Выберите период для топа:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("top_"))
async def top_callback(callback: CallbackQuery):
    period = callback.data.split("_")[1]
    top_data = await get_top(callback.message.chat.id, period, limit=10)
    
    if not top_data:
        await callback.message.edit_text("📊 Статистика пока пуста.")
        return

    lines = []
    for idx, (user_id, msgs, exp) in enumerate(top_data, 1):
        name = await get_username_or_name(user_id)
        exp_display = exp / 100
        lines.append(f"{idx}. {name} — {format_number(msgs)} сообщ., опыт: {exp_display:.2f}")
    
    period_names = {"day": "день", "week": "неделю", "all": "всё время"}
    text = f"🏆 Топ-10 за {period_names[period]}:\n" + "\n".join(lines)
    await callback.message.edit_text(text)

@router.message(Command("mystats"))
async def cmd_mystats(message: Message):
    stats = await get_user_stats(message.chat.id, message.from_user.id)
    if not stats:
        await message.answer("📊 У вас пока нет статистики в этом чате.")
        return
    
    day, week, all_msgs, exp, warns, custom_rank, hidden_rank = stats
    exp_display = exp / 100
    display_rank = get_display_rank(exp, custom_rank)
    
    text = (
        f"📊 <b>Ваша статистика</b>\n"
        f"👤 Пользователь: {message.from_user.full_name}\n"
        f"📅 Сегодня: {format_number(day)} сообщ.\n"
        f"📆 За неделю: {format_number(week)} сообщ.\n"
        f"⌛ Всего: {format_number(all_msgs)} сообщ.\n"
        f"⭐ Опыт: {exp_display:.2f}\n"
        f"🏅 Ранг: {display_rank}\n"
        f"⚠️ Предупреждений: {warns}"
    )
    
    if custom_rank:
        text = "👑 " + text
    
    await message.answer(text)

@router.message(Command("rank"))
async def cmd_rank(message: Message):
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    
    stats = await get_user_stats(message.chat.id, target.id)
    if not stats:
        await message.answer(f"❌ У пользователя {target.full_name} нет статистики.")
        return
    
    day, week, all_msgs, exp, warns, custom_rank, hidden_rank = stats
    exp_display = exp / 100
    display_rank = get_display_rank(exp, custom_rank)
    
    text = (
        f"👤 <b>Пользователь:</b> {target.full_name}\n"
        f"📊 <b>Сообщений всего:</b> {format_number(all_msgs)}\n"
        f"⭐ <b>Опыт:</b> {exp_display:.2f}\n"
        f"🏅 <b>Ранг:</b> {display_rank}\n"
        f"⚠️ <b>Предупреждений:</b> {warns}"
    )
    
    if custom_rank:
        text = "👑 " + text
    
    await message.answer(text)

@router.message(Command("hiddenrank"))
async def cmd_hidden_rank(message: Message):
    if not await is_admin(message.bot, message.chat.id, message.from_user.id):
        return
    
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT hidden_rank, messages_all, messages_day, messages_week
            FROM chat_stats 
            WHERE chat_id = ? AND user_id = ?
        ''', (message.chat.id, target.id))
        row = await cursor.fetchone()
    
    if not row:
        await message.answer("❌ Нет данных о пользователе.")
        return
    
    hidden_rank, all_msgs, day_msgs, week_msgs = row
    from utils import get_hidden_rank_name
    rank_name = get_hidden_rank_name(hidden_rank)
    
    text = (
        f"🔍 <b>Скрытый ранг {target.full_name}</b>\n"
        f"Ранг: {rank_name} (уровень {hidden_rank})\n"
        f"Всего сообщений: {format_number(all_msgs)}\n"
        f"За день: {format_number(day_msgs)}\n"
        f"За неделю: {format_number(week_msgs)}"
    )
    await message.answer(text)