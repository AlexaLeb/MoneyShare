from __future__ import annotations
from typing import Optional, List
from sqlmodel import Session, select
from repositories.base import TransactionParticipantsRepo
from models.transaction_participants import TransactionParticipant
from models.crud.crud_transaction_participants import (
    create_participant, get_participant, list_participants, delete_participant,
)


class TransactionParticipantsRepoSqlModel(TransactionParticipantsRepo):
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, *, transaction_id: int, user_id: int, share_amount: float, tag: str) -> TransactionParticipant:
        return create_participant(self.session, transaction_id=transaction_id, user_id=user_id, share_amount=share_amount, tag=tag)

    def get(self, id: int) -> Optional[TransactionParticipant]:
        return get_participant(self.session, id)

    def list_by_transaction(self, *, transaction_id: int) -> List[TransactionParticipant]:
        # если у тебя есть list_participants(session, transaction_id=...), то можно вызывать его напрямую
        return list_participants(self.session, transaction_id=transaction_id)

    def delete(self, *, id: int) -> bool:
        return delete_participant(self.session, id=id)

    def delete_by_transaction(self, *, transaction_id: int) -> int:
        # Быстрое удаление всех участников транзакции (если такого CRUD нет)
        stmt = select(TransactionParticipant).where(TransactionParticipant.transaction_id == transaction_id)
        to_delete = self.session.exec(stmt).all()
        count = 0
        for p in to_delete:
            self.session.delete(p)
            count += 1
        return count
