import asyncio
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from bot.handlers import all_routers
from bot.middlewares.db_session import DBSessionMiddleware
from database.config import get_settings
from database.database import ensure_schema


async def run():
    ensure_schema()
    settings = get_settings()
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(
            parse_mode=ParseMode.HTML,
            # disable_web_page_preview=True,   # если нужно
            # protect_content=True,            # если нужно
        ),
    )
    dp = Dispatcher()
    # мидлварь сессии БД
    dp.message.middleware(DBSessionMiddleware())
    dp.callback_query.middleware(DBSessionMiddleware())

    for router in all_routers:
        dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run())
