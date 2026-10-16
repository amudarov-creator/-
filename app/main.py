import asyncio
from aiogram import Bot, Dispatcher
from app.bot.handlers import router
from app.core.config import get_settings
from app.core.logging import configure_logging


async def main() -> None:
    configure_logging()
    token = get_settings().telegram_bot_token
    if not token: raise RuntimeError("TELEGRAM_BOT_TOKEN is required")
    bot = Bot(token)
    dp = Dispatcher(); dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__": asyncio.run(main())
