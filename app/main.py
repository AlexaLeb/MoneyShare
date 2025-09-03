# demo_services.py
from __future__ import annotations

from contextlib import contextmanager
from typing import List, Tuple

from sqlmodel import Session

# ⚙️ твоя инфраструктура
from database.database import engine, init_db, get_session

# 🧱 репозитории
from repositories import (
    UsersRepoSqlModel,
    ChatsRepoSqlModel,
    TransactionsRepoSqlModel,
    TransactionParticipantsRepoSqlModel,
    DebtsRepoSqlModel,
)

# 💼 сервисный слой (то, что мы писали: пересчёт долгов, оптимизация переводов и т.д.)
# Если у тебя имена другие, поправь импорты/классы ниже.
from services.debts_service import DebtsService
from services.transactions_service import TransactionsService


@contextmanager
def session_scope():
    """Простой контекстный менеджер для сессии."""
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise


def print_header(title: str):
    print("\n" + "=" * 20, title, "=" * 20)


def print_users(users):
    for u in users:
        print(f"  id={u.id:>6} | username={u.username!s:>12} | first_name={u.first_name!s}")


def print_chats(chats):
    for c in chats:
        print(f"  id={c.id:>6} | title={c.title!s}")


def print_transactions(rows):
    for t in rows:
        print(
            f"  id={t.id:>3} | chat_id={t.chat_id:>6} | creator_id={t.creator_id:>6} | "
            f"amount={t.amount:>8.2f} | title={t.title!s}"
        )


def print_participants(rows):
    for p in rows:
        print(
            f"  id={p.id:>3} | tx_id={p.transaction_id:>3} | user_id={p.user_id:>6} | "
            f"share={p.share_amount:>8.2f} | tag={p.tag}"
        )


def print_debts(rows):
    for d in rows:
        # важный момент: мы печатаем только то, что уже загружено (без ленивых колбэков)
        print(
            f"  id={d.id:>3} | chat_id={d.chat_id:>6} | user_id={d.user_id:>6} | "
            f"amount={d.amount:>8.2f} | updated_at={d.updated_at}"
        )


def print_settlements(ops: List[Tuple[int, int, float]]):
    if not ops:
        print("  (ничего переводить не нужно — все в нуле)")
    for frm, to, amt in ops:
        print(f"  {frm} -> {to} : {amt:.2f}")


def main():
    # Полный reset схемы (для демо; на живой БД так не делаем — используем миграции):
    init_db()

    with session_scope() as s:
        # --- Репозитории (конкретные реализации) ---
        users_repo = UsersRepoSqlModel(s)
        chats_repo = ChatsRepoSqlModel(s)
        tx_repo = TransactionsRepoSqlModel(s)
        parts_repo = TransactionParticipantsRepoSqlModel(s)
        debts_repo = DebtsRepoSqlModel(s)

        # и сервисы

        # --- Сервисы (им нужны Session и репозитории) ---
        tx_service = TransactionsService(
            session=s,
            tx_repo=tx_repo,
            parts_repo=parts_repo,
            debts_repo=debts_repo,
        )
        debt_service = DebtsService(
            session=s,
            debts_repo=debts_repo,
            tx_repo=tx_repo,
            parts_repo=parts_repo,
            users_repo=users_repo,  # пригодится для фич, где нужны данные о пользователях
        )


        # === 1) создаём пользователей и чат
        print_header("Создаём пользователей и чат")
        u1 = users_repo.create(id=111, username="vasya", first_name="Вася")
        u2 = users_repo.create(id=222, username="petya", first_name="Петя")
        u3 = users_repo.create(id=333, username="masha", first_name="Маша")

        chat = chats_repo.create(id=-1001, title="Test Chat")

        print_users(users_repo.list(limit=100, offset=0))
        print_chats(chats_repo.list(limit=100, offset=0))

        # === 2) создаём 2 транзакции и участников
        print_header("Создаём транзакции и участников")
        # Тx1: создатель 111, сумма 1000, участники 222:500, 333:500 (пицца)
        tx1 = tx_service.create_transaction(
            chat_id=chat.id, creator_id=u1.id, amount=1000.0, title="Пицца")
        p1 = tx_service.add_participant(
            transaction_id=tx1.id, user_id=u2.id, share_amount=500.0, tag="пицца"
        )
        p2 = tx_service.add_participant(
            transaction_id=tx1.id, user_id=u3.id, share_amount=500.0, tag="пицца"
        )

        # Tx2: создатель 222, сумма 900, участники 111:450, 333:450 (ужин)
        tx2 = tx_service.create_transaction_with_participants(
            chat_id=chat.id, creator_id=u2.id, amount=900.0, title="Ужин", participants=[222, 333]
        )

        print_transactions(tx_repo.list_by_chat(chat_id=chat.id))
        print_participants(parts_repo.list_by_transaction(transaction_id=tx1.id))
        print_participants(parts_repo.list_by_transaction(transaction_id=tx2[0].id))

        # === 3) пересчёт долгов по чату
        print_header("Пересчитываем долги по чату")
        debt_service.recompute_chat_balances(chat_id=chat.id)

        print_header("Текущие долги (по чату)")
        debts_rows = debts_repo.list_by_chat(chat_id=chat.id, limit=1000, offset=0)
        print_debts(debts_rows)

        # === 4) оптимальные расчёты (кто кому сколько перевести)
        print_header("Оптимальные переводы для закрытия долгов")
        settlements = debt_service.optimize_settlements(chat_id=chat.id)
        print_settlements(settlements)

        # === 5) удалим одного участника у второй транзакции и пересчитаем
        print_header("Удалим участника (u3) из второй транзакции и пересчитаем")
        tx_service.remove_participant(id=p4.id)

        debt_service.recompute_chat_balances(chat_id=chat.id)
        print_header("Долги после удаления участника")
        print_debts(debts_repo.list_by_chat(chat_id=chat.id, limit=1000, offset=0))

        # === 6) удалим целиком первую транзакцию и пересчитаем
        print_header("Удалим первую транзакцию и пересчитаем")
        tx_service.delete(id=tx1.id)

        debt_service.recompute_chat_balances(chat_id=chat.id)
        print_header("Долги после удаления транзакции")
        print_debts(debts_repo.list_by_chat(chat_id=chat.id, limit=1000, offset=0))

        # === 7) финальные оптимальные переводы
        print_header("Финальные оптимальные переводы")
        final_settlements = debt_service.optimize_settlements(chat_id=chat.id)
        print_settlements(final_settlements)

    print_header("Готово")


if __name__ == "__main__":
    main()
