"""
Repo smoke test: проверяем, что репозитории живые и цепочка от БД до сервисного слоя работает.
Скрипт:
  1) чистит БД (init_db)
  2) создаёт пользователей и чат
  3) создаёт транзакцию, участников, апдейтит долги (через upsert_delta)
  4) выводит всё на экран
  5) делает пару обновлений и удалений, снова печатает
Запуск:
  - локально:         python -m app.scripts.repo_smoke_test
  - в Docker (app):   docker compose exec app python -m app.scripts.repo_smoke_test
"""

from datetime import datetime
from pprint import pprint

from database.database import init_db

# используем unit_of_work, который мы добавляли ранее.
# если у тебя его нет — можно временно заменить на next(get_session()).
try:
    from database.database import unit_of_work
    HAS_UOW = True
except Exception:
    from database.database import get_session
    HAS_UOW = False

from repositories import (
    UsersRepoSqlModel,
    ChatsRepoSqlModel,
    TransactionsRepoSqlModel,
    TransactionParticipantsRepoSqlModel,
    DebtsRepoSqlModel,
)


def run_with_session(fn):
    """
    Хелпер, чтобы одинаково работать и с unit_of_work(), и с get_session().
    """
    if HAS_UOW:
        with unit_of_work() as session:
            return fn(session)
    else:
        # генератор get_session() -> берём одну сессию
        session = next(get_session())
        try:
            result = fn(session)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def print_header(title: str):
    print("\n" + "=" * 20 + f" {title} " + "=" * 20)


def main():
    # 1) Полностью пересоздаём схему (для чистоты прогона)
    init_db()

    # Константы теста
    CHAT_ID = -1001
    CREATOR_ID = 111
    USER_B_ID = 222
    USER_C_ID = 333

    print_header("Создаём базовые сущности (users, chat)")

    def step_create_users_and_chat(session):
        users = UsersRepoSqlModel(session)
        chats = ChatsRepoSqlModel(session)

        u_creator = users.create(id=CREATOR_ID, username="vasya", first_name="Вася")
        u_b = users.create(id=USER_B_ID, username="petya", first_name="Петя")
        u_c = users.create(id=USER_C_ID, username="masha", first_name="Маша")

        chat = chats.create(id=CHAT_ID, title="Test Chat")
        return u_creator, u_b, u_c, chat

    u_creator, u_b, u_c, chat = run_with_session(step_create_users_and_chat)
    print("Users:", u_creator, u_b, u_c, sep="\n  ")
    print("Chat:", chat)

    print_header("Создаём транзакцию + участников + долги")

    def step_create_tx_parts_debts(session):
        txs = TransactionsRepoSqlModel(session)
        parts = TransactionParticipantsRepoSqlModel(session)
        debts = DebtsRepoSqlModel(session)

        # транзакция: автор заплатил 900 за двоих друзей (по 450)
        tx = txs.create(chat_id=CHAT_ID, creator_id=CREATOR_ID, amount=900.0, title="Ужин " + datetime.utcnow().strftime("%H:%M:%S"))
        tx_id = tx.id

        share = 900.0 / 2
        p_b = parts.create(transaction_id=tx.id, user_id=USER_B_ID, share_amount=share, tag="ужин")
        p_c = parts.create(transaction_id=tx.id, user_id=USER_C_ID, share_amount=share, tag="ужин")

        # долги: друзья должны (отрицательные долги), автору — положительный баланс
        debts.upsert_delta(chat_id=CHAT_ID, user_id=USER_B_ID, delta=-share)
        debts.upsert_delta(chat_id=CHAT_ID, user_id=USER_C_ID, delta=-share)
        debts.upsert_delta(chat_id=CHAT_ID, user_id=CREATOR_ID, delta=+900.0)

        return tx_id, [p_b, p_c]

    tx_id, participants = run_with_session(step_create_tx_parts_debts)
    print("Transaction:", tx_id)
    print("Participants:")
    for p in participants:
        print("  ", p)

    print_header("Печатаем долги по чату")

    def step_list_debts(session):
        debts = DebtsRepoSqlModel(session)
        rows = debts.list_by_chat(chat_id=CHAT_ID, limit=100, offset=0)
        return [
            {"user_id": d.user_id, "amount": d.amount, "updated_at": d.updated_at}
            for d in rows
        ]

    debts_rows = run_with_session(step_list_debts)
    for d in debts_rows:
        print(d)
        print("  ", f"user_id={d['user_id']:>6} | amount={d['amount']:>8.2f} | updated_at={d['updated_at']}")

    print_header("Маленький апдейт: частичное погашение долга пользователя 222 на 200")

    def step_update_partial(session):
        debts = DebtsRepoSqlModel(session)
        # 222 возвращает 200 → его долг становится -450 + 200 = -250
        debts.upsert_delta(chat_id=CHAT_ID, user_id=USER_B_ID, delta=+200.0)
        # и автор получает -200 (его положительный баланс сокращается)
        debts.upsert_delta(chat_id=CHAT_ID, user_id=CREATOR_ID, delta=-200.0)
        rows = debts.list_by_chat(chat_id=CHAT_ID)
        return [
            {"user_id": d.user_id, "amount": d.amount, "updated_at": d.updated_at}
            for d in rows
        ]

    debts_rows2 = run_with_session(step_update_partial)
    for d in debts_rows2:
        print("  ", f"user_id={d['user_id']:>6} | amount={d['amount']:>8.2f} | updated_at={d['updated_at']}")

    print_header("Удалим одного участника и проверим список участников транзакции")

    def step_delete_participant_and_list(session):
        parts = TransactionParticipantsRepoSqlModel(session)
        all_parts = parts.list_by_transaction(transaction_id=tx_id)
        print("Было")
        for p in all_parts:
            print("  ", p)
        if all_parts:
            parts.delete(id=all_parts[0].id)
        rows = parts.list_by_transaction(transaction_id=tx_id)
        print(rows)
        return parts.list_by_transaction(transaction_id=tx_id)

    parts_left = run_with_session(step_delete_participant_and_list)
    print("Остались участники:")
    for p in parts_left:
        print("  ", p)

    print_header("Удалим транзакцию целиком (демо)")

    def step_delete_tx(session):
        txs = TransactionsRepoSqlModel(session)
        ok = txs.delete(id=tx_id)
        return ok

    ok = run_with_session(step_delete_tx)
    print("Удаление транзакции:", "OK" if ok else "нет записи / уже удалена")

    print_header("Готово ✅")


if __name__ == "__main__":
    main()
