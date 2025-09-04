from aiogram import Router, F
from aiogram.types import Message
from bot.utils.ensure_ctx import ensure_user_and_chat
from sqlmodel import Session
from aiogram.filters import Command

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message, db_session: Session):
    text = (
        "📖 <b>Справка по командам</b>\n\n"
        "➕ <b>/addtx</b> (сумма) (название) [@user ...]\n"
        "  Добавить транзакцию.\n"
        "  Пример: <code>/addtx 120 Пицца @vasya @petya</code>\n"
        "  (если никого не указать — долг делится только на тебя).\n\n"

        "💰 <b>/balance</b>\n"
        "  Показать текущие балансы пользователей в чате.\n"
        "  Пример: <code>/balance</code>\n\n"

        "📉 <b>/optimize</b>\n"
        "  Показать минимальный план переводов, чтобы все долги закрылись.\n"
        "  Пример: <code>/optimize</code>\n\n"

        "✅ <b>/settle_all</b>\n"
        "  Автоматически создать транзакции для погашения всех долгов и пересчитать баланс.\n"
        "  Пример: <code>/settle_all</code>\n\n"

        "🚀 <b>/start</b>\n"
        "  Начало работы и короткая инструкция.\n\n"
        
        "👤 <b>/adduser</b>\n"
        "Добавить пользователя в базу.\n"
        "Пример: <code>/adduser</code> [ответ на сообщение]\n\n"
    )
    ensure_user_and_chat(db_session, tg_user=message.from_user, tg_chat=message.chat)
    await message.answer(text, parse_mode="HTML")
