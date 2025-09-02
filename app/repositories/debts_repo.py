# app/repositories/debts_repo.py
from __future__ import annotations
from typing import Optional, List
from sqlmodel import Session, select
from repositories.base import DebtsRepo
from models.debts import Debt
from models.crud.crud_debts import (
    create_debt, get_debt, list_debts, update_debt, delete_debt,
)


class DebtsRepoSqlModel(DebtsRepo):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, chat_id: int, user_id: int, amount: float) -> Debt:
        return create_debt(self.session, chat_id=chat_id, user_id=user_id, amount=amount)

    def get(self, id: int) -> Optional[Debt]:
        return get_debt(self.session, id)

    def get_by_chat_user(self, *, chat_id: int, user_id: int) -> Optional[Debt]:
        # если у тебя есть CRUD-функция, используй её; иначе — прямой запрос
        stmt = select(Debt).where(Debt.chat_id == chat_id, Debt.user_id == user_id)
        return self.session.exec(stmt).first()

    def list_by_chat(self, *, chat_id: int, limit: int = 100, offset: int = 0) -> List[Debt]:
        return list_debts(self.session, chat_id=chat_id, limit=limit, offset=offset)

    def update(self, *, id: int, amount: float) -> Optional[Debt]:
        return update_debt(self.session, id=id, amount=amount)

    def upsert_delta(self, *, chat_id: int, user_id: int, delta: float) -> Debt:
        """
        Удобный метод: найти долг по (chat_id, user_id) и изменить его на delta.
        Если долга нет — создать с amount=delta.
        """
        existing = self.get_by_chat_user(chat_id=chat_id, user_id=user_id)
        if existing:
            existing.amount = (existing.amount or 0.0) + float(delta)
            self.session.add(existing)
            # updated_at обновится, если в модели у тебя автозаполнение (или обнови вручную)
            return existing
        else:
            return self.create(chat_id=chat_id, user_id=user_id, amount=float(delta))

    def delete(self, *, id: int) -> bool:
        return delete_debt(self.session, id=id)
