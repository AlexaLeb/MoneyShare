# bot/handlers/transactions.py
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from sqlmodel import Session

from bot.utils.ensure_ctx import ensure_user_and_chat
from repositories import (
    UsersRepoSqlModel,
    TransactionsRepoSqlModel,
    TransactionParticipantsRepoSqlModel,
    DebtsRepoSqlModel,
)
from services.transactions_service import TransactionsService
from services.debts_service import DebtsService
from bot.utils.formatting import format_user

router = Router()


def build_services(session: Session):
    users = UsersRepoSqlModel(session)
    txs = TransactionsRepoSqlModel(session)
    parts = TransactionParticipantsRepoSqlModel(session)
    debts = DebtsRepoSqlModel(session)

    tx_service = TransactionsService(
        session=session,
        tx_repo=txs,
        parts_repo=parts,
        debts_repo=debts,
    )
    debts_service = DebtsService(
        session=session,
        debts_repo=debts,
        tx_repo=txs,
        parts_repo=parts,
        users_repo=users,
    )
    return users, txs, parts, tx_service, debts_service


@router.message(Command("history"))
async def cmd_history(message: Message, db_session: Session):
    """
    /history [N] — показать последние N транзакций чата (по умолчанию 20).
    """
    ensure_user_and_chat(db_session, tg_user=message.from_user, tg_chat=message.chat)
    users_repo, txs_repo, parts_repo, _, _ = build_services(db_session)

    chat_id = message.chat.id

    # Попробуем вытащить лимит из команды: "/history 10"
    limit = 20
    try:
        parts = (message.text or "").split()
        if len(parts) >= 2:
            limit = max(1, min(100, int(parts[1])))
    except Exception:
        pass

    tx_list = txs_repo.list_by_chat(chat_id=chat_id, limit=limit, offset=0)
    if not tx_list:
        await message.answer("В этом чате ещё нет транзакций.")
        return

    lines = []
    for tx in tx_list:
        creator = format_user(tx.creator_id, users_repo)
        title = tx.title or "Без названия"
        lines.append(f"#{tx.id} • {title}\n  Сумма: {tx.amount:.2f}\n  Создатель: {creator}")

        parts = parts_repo.list_by_transaction(transaction_id=tx.id)
        if parts:
            p_lines = []
            for p in parts:
                who = format_user(p.user_id, users_repo)
                p_lines.append(f"    — {who}: {p.share_amount:.2f} ({p.tag})")
            lines.append("  Участники:\n" + "\n".join(p_lines))
        else:
            lines.append("  Участников нет")

    text = "Последние транзакции:\n\n" + "\n\n".join(lines)
    # Без HTML/Markdown, чтобы не ловить ошибок парсинга
    await message.answer(text)


@router.message(Command("del"))
async def cmd_delete(message: Message, db_session: Session):
    """
    /del <id> — удалить транзакцию по идентификатору.
    Удаляет участников и саму транзакцию, затем пересчитывает балансы.
    """
    ensure_user_and_chat(db_session, tg_user=message.from_user, tg_chat=message.chat)
    users_repo, txs_repo, parts_repo, tx_service, debts_service = build_services(db_session)

    chat_id = message.chat.id

    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("Формат: /del &lt;id_транзакции&gt;")
        return

    try:
        tx_id = int(parts[1])
    except ValueError:
        await message.answer("ID транзакции должен быть числом. Пример: /del 42")
        return

    tx = txs_repo.get(tx_id)
    if not tx:
        await message.answer(f"Транзакция #{tx_id} не найдена.")
        return
    if int(tx.chat_id) != int(chat_id):
        await message.answer("Нельзя удалить транзакцию из другого чата.")
        return

    ok = tx_service.delete_transaction(transaction_id=tx_id)
    if not ok:
        await message.answer("Не удалось удалить транзакцию (внутренняя ошибка).")
        return

    # Пересчёт балансов
    debts_service.rebuild(chat_id=chat_id)

    await message.answer(f"Транзакция #{tx_id} удалена, балансы пересчитаны.")