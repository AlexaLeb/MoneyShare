from repositories.users_repo import SQLModelUsersRepo
from repositories.chats_repo import SQLModelChatsRepo
from repositories.transactions_repo import SQLModelTransactionsRepo
from repositories.transaction_participants_repo import SQLModelTransactionParticipantsRepo
from repositories.debts_repo import SQLModelDebtsRepo


def _seed_basic(session):
    users = SQLModelUsersRepo(session)
    chats = SQLModelChatsRepo(session)

    u_creator = users.create(id=111, username="creator", first_name="Крис")
    u_bob     = users.create(id=222, username="bob", first_name="Боб")
    u_alice   = users.create(id=333, username="alice", first_name="Алиса")
    chat      = chats.create(id=1001, title="Test Chat")

    return u_creator, u_bob, u_alice, chat


def test_transaction_participants_debts_flow(session):
    users = SQLModelUsersRepo(session)
    chats = SQLModelChatsRepo(session)
    txs   = SQLModelTransactionsRepo(session)
    parts = SQLModelTransactionParticipantsRepo(session)
    debts = SQLModelDebtsRepo(session)

    creator, bob, alice, chat = _seed_basic(session)

    # создаем транзакцию на 900
    tx = txs.create(chat_id=chat.id, creator_id=creator.id, amount=900.0, title="ужин")
    assert tx.id is not None

    # участники по 450
    p1 = parts.create(transaction_id=tx.id, user_id=bob.id,   share_amount=450.0, tag="ужин")
    p2 = parts.create(transaction_id=tx.id, user_id=alice.id, share_amount=450.0, tag="ужин")

    # создаем долги в чате (в примере ты делаешь это отдельно)
    d_bob   = debts.create(chat_id=chat.id, user_id=bob.id,   amount=-450.0)
    d_alice = debts.create(chat_id=chat.id, user_id=alice.id, amount=-450.0)

    # проверим что репо возвращает корректно
    got_parts = parts.list_by_transaction(transaction_id=tx.id)
    assert len(got_parts) == 2

    got_debts = debts.list_by_chat(chat_id=chat.id, limit=10, offset=0)
    assert { (d.user_id, round(d.amount, 2)) for d in got_debts } == {
        (bob.id, -450.0), (alice.id, -450.0)
    }

    # удалим одного участника и поправим долг
    parts.delete(id=p2.id)
    debts.update(id=d_alice.id, amount=0.0)
    left = parts.list_by_transaction(transaction_id=tx.id)
    assert len(left) == 1
    assert left[0].user_id == bob.id

    # удаляем оставшегося участника, потом транзакцию (сначала участники, потом транзакция)
    parts.delete(id=p1.id)
    ok_tx = txs.delete(id=tx.id)
    assert ok_tx is True

    # долговая запись Боба остается (мы удаляем транзакцию, но долги — «актуальное состояние»), проверим апдейт
    debts.update(id=d_bob.id, amount=-300.0)
    d_bob_new = debts.get(id=d_bob.id)
    assert round(d_bob_new.amount, 2) == -300.0