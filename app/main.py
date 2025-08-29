import pydantic, sqlmodel, pydantic_settings

from sqlmodel import create_engine, Session, SQLModel
from database.database import get_session, init_db


from models.crud.crud_users import *
from models.crud.crud_chats import *
from models.crud.crud_transactions import *
from models.crud.crud_transaction_participants import *
from models.crud.crud_debts import *
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)
# Создаём in-memory базу для теста
# engine = create_engine("sqlite:///:memory:", echo=True)

# Создаём все таблицы
# SQLModel.metadata.create_all(engine)
init_db()
session = next(get_session())
print("=== USERS ===")
user1 = create_user(session, id=111, username="vasya", first_name="Вася")
user2 = create_user(session, id=222, username="petya", first_name="Петя")
print(list_users(session))

print("\n=== CHAT ===")
chat = create_chat(session, id=-1001, title="Test Chat")
print(list_chats(session))

print("\n=== TRANSACTION ===")
transaction = create_transaction(session, chat_id=chat.id, creator_id=user1.id, amount=1000, title="Пицца")
print(list_transactions(session))

print("\n=== PARTICIPANTS ===")
part1 = create_participant(session, transaction_id=transaction.id, user_id=user2.id, share_amount=500, tag="пицца")
print(list_participants(session))

print("\n=== DEBTS ===")
debt_user2 = create_debt(session, chat_id=chat.id, user_id=user2.id, amount=-500)
print(list_debts(session))

print("\n=== UPDATE USER ===")
update_user(session, id=111, username="vasya_new")
print(get_user(session, 111))

print("\n=== UPDATE DEBT ===")
update_debt(session, id=debt_user2.id, amount=-300)
print(get_debt(session, debt_user2.id))

print("\n=== DELETE PARTICIPANT ===")
delete_participant(session, id=part1.id)
print(list_participants(session))

print("\n=== DELETE TRANSACTION ===")
delete_transaction(session, id=transaction.id)
print(list_transactions(session))
session.commit()
session.close()
logger.warning('ТЕСТ УСПЕШНЫЙ')
