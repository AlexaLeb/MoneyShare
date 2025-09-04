from sqlmodel import Session, select
from models.users import User
from typing import Optional, List, Sequence
from logger.logging import get_logger
from sqlalchemy import func

logger = get_logger(logger_name=__name__)


def create_user(session: Session, id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> User:
    logger.info('Пользователь создан')
    user = User(id=id, username=username, first_name=first_name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user(session: Session, id: int) -> Optional[User]:
    return session.get(User, id)


def update_user(session: Session, id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> Optional[User]:
    user = get_user(session, id)
    if not user:
        return None
    if username is not None:
        user.username = username
    if first_name is not None:
        user.first_name = first_name
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(session: Session, id: int) -> bool:
    user = get_user(session, id)
    if not user:
        return False
    session.delete(user)
    session.commit()
    return True


def list_users(session: Session, limit: int = 100, offset: int = 0) -> List[User]:
    return session.exec(select(User).offset(offset).limit(limit)).all()


def get_user_by_username(session: Session, username: str) -> Optional[User]:
    """Найти пользователя по username (без @), регистронезависимо."""
    uname = username.lstrip("@").lower()
    stmt = select(User).where(func.lower(User.username) == uname).limit(1)
    return session.exec(stmt).first()


def get_users_by_usernames(session: Session, usernames: Sequence[str]) -> List[User]:
    """Найти сразу нескольких пользователей по списку username (без @), регистронезависимо."""
    usernames_clean = [u.lstrip("@").lower() for u in usernames]
    if not usernames_clean:
        return []
    stmt = select(User).where(func.lower(User.username).in_(usernames_clean))
    return list(session.exec(stmt).all())
