# handlers/commands.py

COMMANDS = {
    # Статистика
    "top": ["топ", "top", "топ10", "top10"],
    "mystats": ["моя стата", "моястата", "моя статистика", "mystats", "my stats", "стата"],
    "rank": ["ранг", "rank", "мой ранг", "myrank"],
    
    # Информация
    "admins": ["админы", "admins", "администраторы", "administrators"],
    
    # Модерация
    "mute": ["мут", "mute", "замьютить", "замутить"],
    "unmute": ["размут", "unmute", "размьютить", "снять мут"],
    "kick": ["кик", "kick", "выгнать", "исключить"],
    "ban": ["бан", "ban", "забанить"],
    "unban": ["разбан", "unban", "разбанить"],
    "warn": ["варн", "warn", "предупреждение", "пред"],
    "unwarn": ["разварн", "unwarn", "снять варн", "снять предупреждение"],
    
    # Админ-ранги
    "setrank": ["назначить", "setrank", "назначить ранг", "выдать ранг"],
    "adminranks": ["админ ранги", "adminranks", "ранги админов"],
    "hiddenrank": ["скрытый ранг", "hiddenrank", "секретный ранг"],
    
    # Настройки
    "settings": ["настройки", "settings", "параметры"],
    "set_welcome": ["приветствие", "set welcome"],
    "set_antiflood": ["антифлуд", "antiflood"],
    "set_mute": ["мут время", "set mute"],
    "set_ban": ["бан время", "set ban"]
}

def get_command(text: str) -> str:
    """
    Определяет, является ли текст командой, и возвращает ключ команды.
    Если текст не является командой, возвращает None.
    """
    if not text:
        return None
    
    text = text.lower().strip()
    
    for cmd, variants in COMMANDS.items():
        if text in variants:
            return cmd
    
    if text.startswith('/'):
        cmd_without_slash = text[1:].split()[0].lower()
        for cmd, variants in COMMANDS.items():
            if cmd_without_slash == cmd or cmd_without_slash in variants:
                return cmd
    
    return None

def extract_args(text: str) -> str:
    """Извлекает аргументы из текста команды"""
    if not text:
        return ""
    
    parts = text.split()
    if len(parts) <= 1:
        return ""
    
    text_lower = text.lower()
    
    for cmd, variants in COMMANDS.items():
        for variant in variants:
            if text_lower.startswith(variant):
                args = text[len(variant):].strip()
                return args
    
    if text.startswith('/'):
        return ' '.join(parts[1:])
    
    return ""