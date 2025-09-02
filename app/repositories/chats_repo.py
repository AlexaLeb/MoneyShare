from __future__ import annotations
from typing import Optional, List
from sqlmodel import Session
from repositories.base import ChatsRepo
from models.chats import Chat
from models.crud.crud_chats import (
    create_chat, get_chat, list_chats, update_chat, delete_chat,
)


class ChatsRepoSqlModel(ChatsRepo):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, id: int, title: Optional[str]) -> Chat:
        return create_chat(self.session, id=id, title=title)

    def get(self, id: int) -> Optional[Chat]:
        return get_chat(self.session, id)

    def list(self, *, limit: int = 100, offset: int = 0) -> List[Chat]:
        return list_chats(self.session, limit=limit, offset=offset)

    def update(self, *, id: int, title: Optional[str] = None) -> Optional[Chat]:
        return update_chat(self.session, id=id, title=title)

    def delete(self, *, id: int) -> bool:
        return delete_chat(self.session, id=id)
