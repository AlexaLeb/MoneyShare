from typing import Optional
from sqlmodel import Session
from repositories import ChatsRepo
from models.chats import Chat


class ChatsService:
    """
    Работа с чатами: ensure, обновление title.
    """

    def __init__(self, session: Session, chats_repo: ChatsRepo) -> None:
        self.session = session
        self.chats = chats_repo

    def ensure_chat(self, chat_id: int, title: Optional[str] = None) -> Chat:
        """
        Если чат не существует — создаём.
        Если существует — можем мягко обновить title, если новый пришёл и он отличается.
        """
        existing = self.chats.get(chat_id)
        if existing:
            if title and existing.title != title:
                self.chats.update(id=chat_id, title=title)
            return existing
        return self.chats.create(id=chat_id, title=title)
