from sqlmodel import Session, select
from models.chats import Chat
from typing import Optional, List
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)


def create_chat(session: Session, id: int, title: Optional[str] = None) -> Chat:
    logger.info('Чат создан')
    chat = Chat(id=id, title=title)
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


def get_chat(session: Session, id: int) -> Optional[Chat]:
    return session.get(Chat, id)


def update_chat(session: Session, id: int, title: Optional[str] = None) -> Optional[Chat]:
    logger.info('Чат обновлен')
    chat = get_chat(session, id)
    if not chat:
        return None
    if title is not None:
        chat.title = title
    session.add(chat)
    session.commit()
    session.refresh(chat)
    return chat


def delete_chat(session: Session, id: int) -> bool:
    chat = get_chat(session, id)
    if not chat:
        return False
    session.delete(chat)
    session.commit()
    return True


def list_chats(session: Session, limit: int = 100, offset: int = 0) -> List[Chat]:
    return session.exec(select(Chat).offset(offset).limit(limit)).all()

