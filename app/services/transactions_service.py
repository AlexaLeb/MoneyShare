from __future__ import annotations

from typing import Iterable, Optional, Sequence, Tuple
from sqlmodel import Session
from repositories import (
    TransactionsRepo,
    TransactionParticipantsRepo,
    DebtsRepo,
)
from models.transactions import Transaction
from models.transaction_participants import TransactionParticipant
from datetime import datetime


class TransactionsService:
    """
    Логика вокруг транзакций и участников.
    Здесь мы держим операции, которые затрагивают сразу несколько таблиц.
    """

    def __init__(
        self,
        session: Session,
        tx_repo: TransactionsRepo,
        parts_repo: TransactionParticipantsRepo,
        debts_repo: DebtsRepo,
    ) -> None:
        self.session = session
        self.txs = tx_repo
        self.parts = parts_repo
        self.debts = debts_repo  # пригодится если нужно триггерить пересчёт

    def create_transaction(
        self,
        *,
        chat_id: int,
        creator_id: int,
        amount: float,
        title: Optional[str],
    ) -> Transaction:
        """
        Создаём транзакцию и её участников одной «операцией».
        participants: список кортежей (user_id, share_amount, tag)
        """
        tx = self.txs.create(
            chat_id=chat_id,
            creator_id=creator_id,
            amount=amount,
            title=title,
        )

        return tx

    def create_transaction_with_participants(
        self,
        *,
        chat_id: int,
        creator_id: int,
        amount: float,
        title: Optional[str],
        participants: Sequence[int],
    ) -> tuple[Transaction, list[TransactionParticipant]]:
        """
        Создаём транзакцию и её участников одной «операцией».
        participants: список кортежей (user_id, share_amount, tag)
        """
        tx = self.txs.create(
            chat_id=chat_id,
            creator_id=creator_id,
            amount=amount,
            title=title,
        )

        created_parts: list[TransactionParticipant] = []
        for user_id in participants:
            part = self.parts.create(
                transaction_id=tx.id,
                user_id=user_id,
                share_amount=amount/(len(participants)),
                tag=title or "без указания типа транзакции",
            )
            created_parts.append(part)

        # (опционально) сразу можно пересчитать долги по чату
        # но чаще это делает DebtsService.rebuild(chat_id)
        return tx, created_parts

    def add_participant(
        self,
        *,
        transaction_id: int,
        user_id: int,
        share_amount: float,
        tag: Optional[str] = None,
    ) -> TransactionParticipant:
        """
        Добавляем участника в уже существующую транзакцию.
        """
        # убеждаемся, что транзакция существует
        tx = self.txs.get(transaction_id)
        if not tx:
            raise ValueError(f"Transaction {transaction_id} not found")

        return self.parts.create(
            transaction_id=transaction_id,
            user_id=user_id,
            share_amount=share_amount,
            tag=tag or "без указания типа транзакции",
        )

    def remove_participant(self, *, participant_id: int) -> bool:
        """
        Удаляем участника транзакции.
        """
        return self.parts.delete(id=participant_id)

    def delete_transaction(self, *, transaction_id: int) -> bool:
        """
        Удаляем транзакцию безопасно:
        1) сначала удаляем участников (жёстко),
        2) потом удаляем транзакцию.
        Это избегает NOT NULL конфликтов по FK.
        """
        # Удаление участников
        all_parts = self.parts.list_by_transaction(transaction_id=transaction_id)
        for p in all_parts:
            self.parts.delete(id=p.id)

        # Удаление самой транзакции
        return self.txs.delete(id=transaction_id)
