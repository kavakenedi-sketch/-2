import aiosqlite
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple

logger = logging.getLogger(__name__)
DB_PATH = "iris_clone.db"

async def init_db():
    """Инициализация базы данных"""
    async with aiosqlite.connect(DB_PATH) as db:
        # Пользователи (кэш)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Статистика по чатам
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                messages_day INTEGER DEFAULT 0,
                messages_week INTEGER DEFAULT 0,
                messages_all INTEGER DEFAULT 0,
                experience INTEGER DEFAULT 0,
                warns INTEGER DEFAULT 0,
                custom_rank INTEGER,
                hidden_rank INTEGER DEFAULT 0,
                last_message_time TIMESTAMP,
                rank_updated_at TIMESTAMP,
                UNIQUE(chat_id, user_id)
            )
        ''')
        
        # Настройки чата
        await db.execute('''
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                welcome_enabled INTEGER DEFAULT 1,
                antiflood_enabled INTEGER DEFAULT 1,
                mute_duration INTEGER DEFAULT 60,
                ban_duration INTEGER DEFAULT 3600
            )
        ''')
        
        # Логи модерации
        await db.execute('''
            CREATE TABLE IF NOT EXISTS moderation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                admin_id INTEGER,
                action TEXT,
                target_id INTEGER,
                reason TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Ежедневная статистика (для точного подсчёта за 30 дней)
        await db.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER,
                user_id INTEGER,
                date TEXT,
                messages INTEGER DEFAULT 0,
                UNIQUE(chat_id, user_id, date)
            )
        ''')
        
        await db.commit()
    logger.info("База данных инициализирована")

# --- Работа с пользователями ---
async def update_user_info(user_id: int, username: str = None, first_name: str = None, last_name: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO users (user_id, username, first_name, last_name, updated_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                updated_at=excluded.updated_at
        ''', (user_id, username, first_name, last_name))
        await db.commit()

async def get_user_info(user_id: int) -> Optional[Tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT username, first_name, last_name FROM users WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()

# --- Работа со статистикой ---
async def add_message(chat_id: int, user_id: int, text: str):
    """Начисляет опыт и увеличивает счётчики сообщений"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT messages_day, messages_week, messages_all, experience, warns, custom_rank
            FROM chat_stats WHERE chat_id = ? AND user_id = ?
        ''', (chat_id, user_id))
        row = await cursor.fetchone()

        exp_gain = (len(text) // 3) * 30
        if text and text[0].isupper() and text[-1] in '.!?':
            exp_gain += 20

        today = datetime.now().strftime("%Y-%m-%d")

        if row:
            messages_day, messages_week, messages_all, experience, warns, custom_rank = row
            messages_day += 1
            messages_week += 1
            messages_all += 1
            experience += exp_gain
            
            await db.execute('''
                UPDATE chat_stats
                SET messages_day = ?, messages_week = ?, messages_all = ?, 
                    experience = ?, last_message_time = CURRENT_TIMESTAMP
                WHERE chat_id = ? AND user_id = ?
            ''', (messages_day, messages_week, messages_all, experience, chat_id, user_id))
        else:
            await db.execute('''
                INSERT INTO chat_stats 
                (chat_id, user_id, messages_day, messages_week, messages_all, experience, last_message_time)
                VALUES (?, ?, 1, 1, 1, ?, CURRENT_TIMESTAMP)
            ''', (chat_id, user_id, exp_gain))
        
        await db.execute('''
            INSERT INTO daily_stats (chat_id, user_id, date, messages)
            VALUES (?, ?, ?, 1)
            ON CONFLICT(chat_id, user_id, date) DO UPDATE SET
                messages = messages + 1
        ''', (chat_id, user_id, today))
        
        await db.commit()

async def reset_day_stats():
    """Обнуляет messages_day для всех пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE chat_stats SET messages_day = 0')
        await db.commit()
    logger.info("Дневная статистика сброшена")

async def reset_week_stats():
    """Обнуляет messages_week для всех пользователей"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE chat_stats SET messages_week = 0')
        await db.commit()
    logger.info("Недельная статистика сброшена")

async def get_top(chat_id: int, period: str = 'all', limit: int = 10) -> List[Tuple]:
    period_map = {
        'day': 'messages_day',
        'week': 'messages_week',
        'all': 'messages_all'
    }
    column = period_map.get(period, 'messages_all')
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(f'''
            SELECT user_id, {column}, experience
            FROM chat_stats
            WHERE chat_id = ?
            ORDER BY {column} DESC, experience DESC
            LIMIT ?
        ''', (chat_id, limit))
        return await cursor.fetchall()

async def get_user_stats(chat_id: int, user_id: int) -> Optional[Tuple]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT messages_day, messages_week, messages_all, experience, warns, custom_rank, hidden_rank
            FROM chat_stats WHERE chat_id = ? AND user_id = ?
        ''', (chat_id, user_id))
        return await cursor.fetchone()

async def set_custom_rank(chat_id: int, user_id: int, rank: Optional[int]):
    """Устанавливает админ-ранг (custom_rank)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO chat_stats (chat_id, user_id, custom_rank)
            VALUES (?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET custom_rank=excluded.custom_rank
        ''', (chat_id, user_id, rank))
        await db.commit()

async def update_hidden_rank(chat_id: int, user_id: int) -> Optional[int]:
    """
    Проверяет условия и обновляет скрытый ранг пользователя.
    Возвращает новый ранг или None, если ранг не изменился.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT messages_all, messages_day, messages_week, hidden_rank
            FROM chat_stats 
            WHERE chat_id = ? AND user_id = ?
        ''', (chat_id, user_id))
        row = await cursor.fetchone()
        if not row:
            return None
        
        all_msgs, day_msgs, week_msgs, current_hidden = row
        
        thirty_days_ago = (datetime.now().date() - timedelta(days=30)).strftime("%Y-%m-%d")
        cursor = await db.execute('''
            SELECT SUM(messages) FROM daily_stats
            WHERE chat_id = ? AND user_id = ? AND date >= ?
        ''', (chat_id, user_id, thirty_days_ago))
        month_msgs = (await cursor.fetchone())[0] or 0
        
        new_rank = 0
        
        if all_msgs >= 1:
            new_rank = 1
        if all_msgs >= 1000:
            new_rank = 2
        if day_msgs >= 5000:
            new_rank = 3
        if week_msgs >= 15000:
            new_rank = 4
        if week_msgs >= 35000:
            new_rank = 5
        if month_msgs >= 100000:
            new_rank = 6
        
        if new_rank != current_hidden:
            await db.execute('''
                UPDATE chat_stats 
                SET hidden_rank = ?, rank_updated_at = CURRENT_TIMESTAMP
                WHERE chat_id = ? AND user_id = ?
            ''', (new_rank, chat_id, user_id))
            await db.commit()
            return new_rank
        
        return None

async def add_warn(chat_id: int, user_id: int) -> int:
    """Увеличивает счётчик варнов, возвращает текущее количество"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT warns FROM chat_stats WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        row = await cursor.fetchone()
        if row:
            warns = row[0] + 1
            await db.execute('UPDATE chat_stats SET warns = ? WHERE chat_id = ? AND user_id = ?', (warns, chat_id, user_id))
        else:
            warns = 1
            await db.execute('INSERT INTO chat_stats (chat_id, user_id, warns) VALUES (?, ?, ?)', (chat_id, user_id, warns))
        await db.commit()
        return warns

async def remove_warn(chat_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('SELECT warns FROM chat_stats WHERE chat_id = ? AND user_id = ?', (chat_id, user_id))
        row = await cursor.fetchone()
        if row and row[0] > 0:
            warns = row[0] - 1
            await db.execute('UPDATE chat_stats SET warns = ? WHERE chat_id = ? AND user_id = ?', (warns, chat_id, user_id))
        else:
            warns = 0
        await db.commit()
        return warns

# --- Настройки чата ---
async def get_chat_settings(chat_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            SELECT welcome_enabled, antiflood_enabled, mute_duration, ban_duration 
            FROM chat_settings WHERE chat_id = ?
        ''', (chat_id,))
        row = await cursor.fetchone()
        if not row:
            return (1, 1, 60, 3600)
        return row

async def update_chat_setting(chat_id: int, setting: str, value):
    """Обновляет конкретную настройку чата"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f'''
            INSERT INTO chat_settings (chat_id, {setting})
            VALUES (?, ?)
            ON CONFLICT(chat_id) DO UPDATE SET {setting}=excluded.{setting}
        ''', (chat_id, value))
        await db.commit()

# --- Логирование модерации ---
async def log_moderation(chat_id: int, admin_id: int, action: str, target_id: int, reason: str = ""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT INTO moderation_logs (chat_id, admin_id, action, target_id, reason)
            VALUES (?, ?, ?, ?, ?)
        ''', (chat_id, admin_id, action, target_id, reason))
        await db.commit()