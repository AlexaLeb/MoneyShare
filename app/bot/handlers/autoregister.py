# bot/handlers/autoregister.py
from pickle import FALSE

from aiogram import Router
from aiogram.types import Message
from sqlmodel import Session
from bot.utils.ensure_ctx import ensure_user_and_chat
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)

router = Router()


@router.message(flags={'block': False})  # реагирует на любое сообщение
async def auto_register(message: Message, db_session: Session):
    """
    Автоматически регистрируем юзера и чат в базе,
    если их ещё не было.
    """
    ensure_user_and_chat(db_session, tg_user=message.from_user, tg_chat=message.chat)
    logger.info("Пользователь проверен")
