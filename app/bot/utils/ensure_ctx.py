# bot/utils/ensure_ctx.py
from repositories import UsersRepoSqlModel, ChatsRepoSqlModel


def ensure_user_and_chat(session, *, tg_user, tg_chat):
    """
    tg_user: aiogram.types.User
    tg_chat: aiogram.types.Chat
    """
    users = UsersRepoSqlModel(session)
    chats = ChatsRepoSqlModel(session)

    # upsert user
    u = users.get(tg_user.id)
    if not u:
        users.create(
            id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
        )

    # upsert chat
    c = chats.get(tg_chat.id)
    if not c:
        chats.create(
            id=tg_chat.id,
            title=tg_chat.title or tg_chat.full_name if hasattr(tg_chat, "full_name") else tg_chat.title,
        )