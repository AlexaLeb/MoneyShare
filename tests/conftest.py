import pytest
from sqlmodel import SQLModel, create_engine, Session


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
    with Session(engine) as s:
        yield s