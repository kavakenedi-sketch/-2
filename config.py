import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("8019928524:AAEA_SYAPK21AQmWR1aAB_u6dqvJq4vUaW8", "8019928524:AAEA_SYAPK21AQmWR1aAB_u6dqvJq4vUaW8")  # Замените на свой токен
    TIMEZONE: str = "Europe/Moscow"
    MUTE_PERIOD: int = 60
    BAN_PERIOD: int = 3600
    MAX_WARNS: int = 3
    ANTIFLOOD_SECONDS: int = 2
    BONUS_GRAMMAR: int = 20