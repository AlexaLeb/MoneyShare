from typing import Callable, Awaitable, Dict, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from contextlib import contextmanager
from sqlmodel import Session
from database.database import engine  # твой engine


@contextmanager
def session_scope():
    session = Session(engine)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class DBSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        # кладём session в data — aiogram прокинет его в хендлер как аргумент
        with session_scope() as session:
            data["db_session"] = session
            return await handler(event, data)
