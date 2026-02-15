from database import get_user_info

ADMIN_RANKS = [
    "Смотрящий",
    "Надзиратель",
    "Хранитель",
    "Страж",
    "Правитель",
    "Властелин"
]

HIDDEN_RANKS = [
    "Новичок",
    "Начинающий",
    "Активный",
    "Эксперт",
    "Легенда",
    "Безумец"
]

def format_number(num: int) -> str:
    """Форматирует число с разделением тысяч"""
    return f"{num:,}".replace(",", " ")

def get_display_rank(experience: int, custom_rank: int = None) -> str:
    """
    Возвращает ранг для отображения пользователю.
    Если есть custom_rank (админ-ранг) — показываем его.
    Иначе показываем "Участник"
    """
    if custom_rank and 1 <= custom_rank <= 6:
        return ADMIN_RANKS[custom_rank - 1]
    return "Участник"

def get_hidden_rank_name(rank: int) -> str:
    """Для внутреннего использования"""
    if 1 <= rank <= 6:
        return HIDDEN_RANKS[rank - 1]
    return "Без ранга"

async def get_username_or_name(user_id: int) -> str:
    info = await get_user_info(user_id)
    if info and info[0]:
        return f"@{info[0]}"
    elif info and (info[1] or info[2]):
        return f"{info[1] or ''} {info[2] or ''}".strip()
    else:
        return f"ID {user_id}"

async def is_admin(bot, chat_id: int, user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором чата"""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in ("creator", "administrator")
    except:
        return False

async def is_creator(bot, chat_id: int, user_id: int) -> bool:
    """Проверяет, является ли пользователь владельцем чата"""
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status == "creator"
    except:
        return False