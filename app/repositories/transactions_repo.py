from __future__ import annotations
from typing import Optional, List
from sqlmodel import Session
from repositories.base import TransactionsRepo
from models.transactions import Transaction
from models.crud.crud_transactions import (
    create_transaction, get_transaction, list_transactions, delete_transaction,
)


class TransactionsRepoSqlModel(TransactionsRepo):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, chat_id: int, creator_id: int, amount: float, title: Optional[str]) -> Transaction:
        return create_transaction(self.session, chat_id=chat_id, creator_id=creator_id, amount=amount, title=title)

    def get(self, id: int) -> Optional[Transaction]:
        return get_transaction(self.session, id)

    def list_by_chat(self, *, chat_id: int, limit: int = 100, offset: int = 0) -> List[Transaction]:
        return list_transactions(self.session, chat_id=chat_id, limit=limit, offset=offset)

    def delete(self, *, id: int) -> bool:
        return delete_transaction(self.session, id=id)