from typing import Optional
from sqlmodel import Session
from repositories import UsersRepo
from models.users import User


class UsersService:
    """
    Работа с пользователями: ensure, поиск, обновления.
    """

    def __init__(self, session: Session, users_repo: UsersRepo) -> None:
        self.session = session
        self.users = users_repo

    def ensure_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
    ) -> User:
        """
        Если пользователя нет — создаём. Если есть — при необходимости обновляем видимые поля.
        """
        existing = self.users.get(user_id)
        if existing:
            # Опциональное обновление «мягких» полей
            need_update = False
            if username and existing.username != username:
                existing.username = username
                need_update = True
            if first_name and existing.first_name != first_name:
                existing.first_name = first_name
                need_update = True

            if need_update:
                # Репозиторий инкапсулирует commit/flush как ты настроил
                self.users.update(
                    id=existing.id,
                    username=existing.username,
                    first_name=existing.first_name,
                )
            return existing

        # Создаём нового
        return self.users.create(id=user_id, username=username, first_name=first_name)
