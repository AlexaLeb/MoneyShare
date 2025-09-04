# bot/handlers/users.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlmodel import Session

from bot.utils.ensure_ctx import ensure_user_and_chat
from repositories import (
    UsersRepoSqlModel,
    ChatsRepoSqlModel,
)

router = Router()


@router.message(Command("adduser"))
async def cmd_adduser(message: Message, db_session: Session):
    """
    Использование: ответь на сообщение пользователя и введи /adduser
    Бот добавит (или обновит) этого пользователя в БД и зарегистрирует чат.
    """
    if not message.reply_to_message:
        await message.answer("Сделай /adduser ответом на сообщение нужного пользователя.")
        return

    target = message.reply_to_message.from_user  # тот, кого добавляем
    chat = message.chat

    users_repo = UsersRepoSqlModel(db_session)
    chats_repo = ChatsRepoSqlModel(db_session)

    # проверим, есть ли чат
    chat_row = chats_repo.get(id=chat.id)
    if not chat_row:
        # создаём новый чат, если нет
        ensure_user_and_chat(db_session, tg_user=target, tg_chat=chat)
        chat_row = chats_repo.get(id=chat.id)

    # проверим, есть ли юзер
    user_row = users_repo.get(id=target.id)
    if user_row:
        await message.answer(
            f"Пользователь уже есть в БД:\n"
            f"• id: {user_row.id}\n"
            f"• username: @{user_row.username if user_row.username else '—'}\n"
            f"• name: {user_row.first_name or '—'}"
        )
        return

    # если юзера ещё нет → добавим
    ensure_user_and_chat(db_session, tg_user=target, tg_chat=chat)
    user_row = users_repo.get(id=target.id)

    await message.answer(
        f"Ок! Пользователь добавлен в БД:\n"
        f"• id: {user_row.id}\n"
        f"• username: @{user_row.username if user_row.username else '—'}\n"
        f"• name: {user_row.first_name or '—'}"
    )
