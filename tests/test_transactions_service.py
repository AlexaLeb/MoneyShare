# tests/test_transactions_service.py
from __future__ import annotations

from typing import Sequence, Tuple, Optional
from models.transaction_participants import TransactionParticipant


def _create_tx_with_parts(tx_service, *, chat_id: int, creator_id: int,
                          amount: float, title: Optional[str],
                          participants: Sequence[Tuple[int, float, Optional[str]]]):
    """
    Helper: поддерживает оба варианта API:
    - create_transaction + add_participants_to_transaction
    - create_transaction_with_participants
    """
    if hasattr(tx_service, "create_transaction"):
        tx = tx_service.create_transaction(
            chat_id=chat_id,
            creator_id=creator_id,
            amount=amount,
            title=title,
        )
        if hasattr(tx_service, "add_participants_to_transaction"):
            tx_service.add_participants_to_transaction(
                transaction_id=tx.id,
                participants=participants,
            )
        else:
            # если вдруг метод называется add_participant
            for uid, share, tag in participants:
                tx_service.add_participant(
                    transaction_id=tx.id,
                    user_id=uid,
                    share_amount=share,
                    tag=tag,
                )
        return tx
    else:
        # старый вариант единым методом
        tx, parts = tx_service.create_transaction_with_participants(
            chat_id=chat_id,
            creator_id=creator_id,
            amount=amount,
            title=title,
            participants=participants,
        )
        return tx


def test_create_transaction_and_parts(tx_service, parts_repo, seed_users, seed_chat):
    u1, u2, u3 = seed_users
    chat_id = seed_chat

    tx = _create_tx_with_parts(
        tx_service,
        chat_id=chat_id,
        creator_id=u1,
        amount=1000,
        title="Пицца",
        participants=[
            (u2, 300.0, "пицца"),
            (u3, 700.0, "пицца"),
        ],
    )

    # Проверим, что участники создались корректно
    parts = parts_repo.list_by_transaction(transaction_id=tx.id)
    assert len(parts) == 2
    assert sorted([p.user_id for p in parts]) == sorted([u2, u3])
    assert sum(p.share_amount for p in parts) == 1000.0


def test_add_and_remove_participant(tx_service, parts_repo, seed_users, seed_chat):
    u1, u2, u3 = seed_users
    chat_id = seed_chat

    tx = _create_tx_with_parts(
        tx_service,
        chat_id=chat_id,
        creator_id=u1,
        amount=500,
        title="Такси",
        participants=[(u2, 200.0, "такси")],
    )

    # Добавим участника
    added = tx_service.add_participant(
        transaction_id=tx.id, user_id=u3, share_amount=300.0, tag="такси"
    )
    parts = parts_repo.list_by_transaction(transaction_id=tx.id)
    assert len(parts) == 2
    assert any(p.user_id == u3 and p.share_amount == 300.0 for p in parts)

    # Удалим участника
    ok = tx_service.remove_participant(participant_id=added.id)
    assert ok is True
    parts2 = parts_repo.list_by_transaction(transaction_id=tx.id)
    assert len(parts2) == 1
    assert parts2[0].user_id == u2


def test_delete_transaction(tx_service, parts_repo, seed_users, seed_chat, tx_repo):
    u1, u2, u3 = seed_users
    chat_id = seed_chat

    tx = _create_tx_with_parts(
        tx_service,
        chat_id=chat_id,
        creator_id=u1,
        amount=900,
        title="Ужин",
        participants=[(u2, 400.0, "ужин"), (u3, 500.0, "ужин")],
    )

    # Перед удалением — участники есть
    parts = parts_repo.list_by_transaction(transaction_id=tx.id)
    assert len(parts) == 2

    # Удаляем транзакцию безопасно (сначала участники, потом транзакция)
    ok = tx_service.delete_transaction(transaction_id=tx.id)
    assert ok is True

    # Участников больше нет
    parts2 = parts_repo.list_by_transaction(transaction_id=tx.id)
    assert len(parts2) == 0

    # И транзакции тоже нет
    assert tx_repo.get(tx.id) is None