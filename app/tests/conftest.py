# tests/conftest.py
from __future__ import annotations

import pytest
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel, Session, create_engine

# модели
from models.users import User
from models.chats import Chat
from models.transactions import Transaction
from models.transaction_participants import TransactionParticipant
from models.debts import Debt

# репозитории (конкретные реализации)
from repositories import (
    UsersRepoSqlModel,
    ChatsRepoSqlModel,
    TransactionsRepoSqlModel,
    TransactionParticipantsRepoSqlModel,
    DebtsRepoSqlModel,
)

# сервисы
from services.transactions_service import TransactionsService
from services.debts_service import DebtsService


# ВАЖНО: SQLite in-memory на каждый тест => чистая БД
@pytest.fixture
def engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )
    # Создаем схему
    SQLModel.metadata.create_all(engine)
    # Включаем внешние ключи в SQLite
    with Session(engine) as s:
        s.exec("PRAGMA foreign_keys=ON")
    yield engine
    # Чистим схему (для in-memory не обязательно, но пусть будет)
    SQLModel.metadata.drop_all(engine)


@pytest.fixture
def session(engine):
    """
    Транзакционная сессия на каждый тест: откатываем всё по окончании.
    """
    with Session(engine) as s:
        trans = s.begin()
        try:
            yield s
        finally:
            trans.rollback()

@pytest.fixture
def users_repo(session):
    return UsersRepoSqlModel(session)

@pytest.fixture
def chats_repo(session):
    return ChatsRepoSqlModel(session)

@pytest.fixture
def tx_repo(session):
    return TransactionsRepoSqlModel(session)

@pytest.fixture
def parts_repo(session):
    return TransactionParticipantsRepoSqlModel(session)

@pytest.fixture
def debts_repo(session):
    return DebtsRepoSqlModel(session)


# ---------- Сервисы ----------

@pytest.fixture
def tx_service(session, tx_repo, parts_repo, debts_repo):
    """
    TransactionsService принимает session + конкретные репозитории.
    NB: если у тебя метод называется create_transaction_with_participants,
    тесты ниже учитывают оба варианта (см. helper в тестах).
    """
    return TransactionsService(
        session=session,
        tx_repo=tx_repo,
        parts_repo=parts_repo,
        debts_repo=debts_repo,
    )

@pytest.fixture
def debts_service(session, debts_repo, tx_repo, parts_repo, users_repo):
    return DebtsService(
        session=session,
        debts_repo=debts_repo,
        tx_repo=tx_repo,
        parts_repo=parts_repo,
        users_repo=users_repo,
    )


# ---------- Данные для тестов ----------

@pytest.fixture
def seed_users(users_repo):
    """
    Создаём 3-х пользователей. Возвращаем их id.
    """
    u1 = users_repo.create(id=111, username="vasya", first_name="Вася")
    u2 = users_repo.create(id=222, username="petya", first_name="Петя")
    u3 = users_repo.create(id=333, username="masha", first_name="Маша")
    return u1.id, u2.id, u3.id


@pytest.fixture
def seed_chat(chats_repo):
    ch = chats_repo.create(id=-1001, title="Test Chat")
    return ch.id
