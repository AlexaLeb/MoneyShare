from aiogram import Router, F
from aiogram.enums import MessageEntityType
from aiogram.types import Message
from sqlmodel import Session
from bot.utils.ensure_ctx import ensure_user_and_chat

# репозитории и сервисы из твоего проекта:
from repositories import (
    UsersRepoSqlModel,
    ChatsRepoSqlModel,
    TransactionsRepoSqlModel,
    TransactionParticipantsRepoSqlModel,
    DebtsRepoSqlModel,
)
from services.transactions_service import TransactionsService
from services.debts_service import DebtsService

router = Router()


def build_services(session: Session):
    users = UsersRepoSqlModel(session)
    chats = ChatsRepoSqlModel(session)
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
    return users, chats, tx_service, debts_service


@router.message(F.text == "/start")
async def cmd_start(message: Message, db_session: Session):
    await message.answer("Привет! Я помогу разделять расходы.\nКоманды: /addtx, /balance, /optimize, /settle_all, /help")


@router.message(F.text == "/balance")
async def cmd_balance(message: Message, db_session: Session):
    _, _, _, debts_service = build_services(db_session)
    chat_id = message.chat.id
    rows = debts_service.debts.list_by_chat(chat_id=chat_id, limit=1000, offset=0)
    if not rows:
        await message.answer("Балансов пока нет. Добавь транзакцию: /addtx 100 Пицца @user1 @user2")
        return
    lines = [f"user {d.user_id}: {d.amount:.2f}" for d in rows]
    await message.answer("Текущие балансы:\n" + "\n".join(lines))


@router.message(F.text == "/optimize")
async def cmd_optimize(message: Message, db_session: Session):
    _, _, _, debts_service = build_services(db_session)
    chat_id = message.chat.id
    plan = debts_service.optimize_settlements(chat_id)
    if not plan:
        await message.answer("Долгов нет — всё по нулям!")
        return
    lines = [f"{frm} → {to}: {amount:.2f}" for frm, to, amount in plan]
    await message.answer("Минимальный план переводов:\n" + "\n".join(lines))


@router.message(F.text == "/settle_all")
async def cmd_settle_all(message: Message, db_session: Session):
    _, _, _, debts_service = build_services(db_session)
    chat_id = message.chat.id
    plan = debts_service.settle_all_debts_via_transactions(chat_id)
    if not plan:
        await message.answer("Нечего гасить — долги отсутствуют.")
        return
    await message.answer("Создал транзакции погашения. Пересчитали балансы.\nВведи /balance чтобы посмотреть.")


@router.message(F.text.startswith("/addtx"))
async def cmd_addtx(message: Message, db_session: Session):
    """
    Формат: /addtx <сумма> <название...> [@username ...]
    - Если есть упоминания: доля будет поделена между УПОМИНУТЫМИ пользователями.
      Создатель в участниках НЕ добавляется автоматически (он — кредитор).
    - Если упоминаний нет: участник = сам автор (упрощённо).
    """
    users_repo, _, tx_service, debts_service = build_services(db_session)

    # Убедимся, что текущий юзер и чат есть в БД
    ensure_user_and_chat(db_session, tg_user=message.from_user, tg_chat=message.chat)

    chat_id = message.chat.id
    creator_id = message.from_user.id

    if not message.text:
        await message.answer("Нужна текстовая команда: /addtx &lt;сумма&gt; &lt;название&gt; [@user ...]")
        return

    parts = message.text.split()
    if len(parts) < 3:
        await message.answer("Формат: /addtx &lt;сумма&gt; &lt;название&gt; [@user ...]")
        return

    # 1) сумма
    try:
        amount = float(parts[1].replace(",", "."))
    except ValueError:
        await message.answer("Сумма должна быть числом. Пример: /addtx 120.5 Ужин @vasya @petya")
        return

    # 2) Собираем упоминания из entities (и @username, и text_mention)
    typed_mentions: set[int] = set()  # ID из text_mention (уверенный источник)
    at_usernames: list[str] = []      # @username (надо резолвить через БД)

    # Парсим entities — это точнее, чем просто искать "@"
    if message.entities:
        for ent in message.entities:
            if ent.type == MessageEntityType.TEXT_MENTION and ent.user:
                typed_mentions.add(ent.user.id)
                tg = ent.use

                # upsert напрямую через сессию
                db_user = users_repo.get(tg.id)
                if db_user is None:
                    db_user = users_repo.create(
                        id=tg.id,
                        username=tg.username,
                        first_name=tg.first_name
                    )
                    db_session.add(db_user)
                else:
                    # обновим, если что-то поменялось
                    changed = False
                    if db_user.username != tg.username:
                        db_user.username = tg.username
                        changed = True
                    if db_user.first_name != tg.first_name:
                        db_user.first_name = tg.first_name
                        changed = True
                    if changed:
                        db_session.add(db_user)

            elif ent.type == MessageEntityType.MENTION:
                # вырезаем "@name" из текста по offsets
                uname = message.text[ent.offset: ent.offset + ent.length]
                at_usernames.append(uname.lstrip("@"))

    # 3) Выделим хвост после суммы и уберём из него все упоминания — получим title
    #    Простой способ: возьмём все слова после суммы и отбросим те, что начинаются с '@'.
    tail_tokens = parts[2:]  # всё после суммы
    title_words = [t for t in tail_tokens if not t.startswith("@")]
    title = " ".join(title_words).strip() or "Без названия"

    # 4) резолвим @username → user_id через БД
    resolved_ids = set(typed_mentions)
    unknown_usernames = []
    if at_usernames:
        # Можно разом: users_repo.get_many_by_usernames
        found_users = users_repo.get_many_by_usernames(at_usernames)
        by_uname = {u.username.lower(): u for u in found_users if u.username}

        for uname in at_usernames:
            u = by_uname.get(uname.lower())
            if u:
                resolved_ids.add(int(u.id))
            else:
                unknown_usernames.append(uname)

    if unknown_usernames:
        await message.answer(
            "Не смог распознать пользователей: " +
            ", ".join(f"@{u}" for u in unknown_usernames) +
            "\nПопроси их написать любое сообщение в чат (или упомяни через 'text mention' из контактов), и повтори команду."
        )
        return

    # 5) формируем участников
    participants = []
    if resolved_ids:
        # делим сумму поровну между упомянутыми
        share = round(amount / len(resolved_ids), 2)
        # чтобы суммарно совпало, последнему можно докинуть «хвостик»
        ids_list = list(resolved_ids)
        tail_fix = round(amount - share * len(ids_list), 2)
        for idx, uid in enumerate(ids_list):
            s = share + (tail_fix if idx == len(ids_list) - 1 else 0.0)
            participants.append((uid, s, "ручной ввод"))
    else:
        # нет упоминаний — участник = сам автор
        participants = [(creator_id, amount, "ручной ввод")]

    # 5) создаём транзакцию + добавляем участников
    tx = tx_service.create_transaction_with_participants(
        chat_id=chat_id,
        creator_id=creator_id,
        amount=amount,
        title=title,
        participants=participants
    )

    # 6) пересчитываем балансы
    debts_service.rebuild(chat_id=chat_id)

    await message.answer(f"Ок! Добавил транзакцию: {amount:.2f} — {title}")
