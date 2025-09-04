from __future__ import annotations
from typing import Optional, List, Sequence
from sqlmodel import Session
from repositories.base import UsersRepo, RepositoryError
from models.users import User
from models.crud.crud_users import (
    create_user, get_user, list_users, update_user, delete_user, get_user_by_username, get_users_by_usernames,
)


class UsersRepoSqlModel(UsersRepo):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, id: int, username: Optional[str], first_name: Optional[str]) -> User:
        return create_user(self.session, id=id, username=username, first_name=first_name)

    def get(self, id: int) -> Optional[User]:
        return get_user(self.session, id)

    def list(self, *, limit: int = 100, offset: int = 0) -> List[User]:
        return list_users(self.session, limit=limit, offset=offset)

    def update(self, *, id: int, username: Optional[str] = None, first_name: Optional[str] = None) -> Optional[User]:
        return update_user(self.session, id=id, username=username, first_name=first_name)

    def delete(self, *, id: int) -> bool:
        return delete_user(self.session, id=id)

    def get_by_username(self, username: str) -> Optional[User]:
        return get_user_by_username(self.session, username)

    def get_many_by_usernames(self, usernames: Sequence[str]) -> List[User]:
        return get_users_by_usernames(self.session, usernames)
