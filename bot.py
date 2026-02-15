import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties  # Исправленный импорт
from aiogram.enums import ParseMode
from aiogram.types import Message

from config import Config
from database import init_db
from scheduler import start_scheduler
from middlewares import AntifloodMiddleware, LoggingMiddleware
from filters import IsPrivate
from handlers import group, stats, moderation, ranks, admin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

config = Config()
bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.message.middleware(AntifloodMiddleware(default_delay=config.ANTIFLOOD_SECONDS))
dp.message.middleware(LoggingMiddleware())

@dp.message(IsPrivate())
async def private_not_allowed(message: Message):
    await message.answer("🤖 Бот работает только в группах.")

dp.include_router(stats.router)
dp.include_router(moderation.router)
dp.include_router(ranks.router)
dp.include_router(admin.router)
dp.include_router(group.router)

@dp.startup()
async def on_startup():
    await init_db()
    start_scheduler()
    logger.info("✅ Бот запущен")

@dp.shutdown()
async def on_shutdown():
    logger.info("❌ Бот остановлен")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
