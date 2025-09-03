# services/debts_service.py
from __future__ import annotations

from typing import Dict, List, Tuple
from sqlmodel import Session
from repositories import DebtsRepo, TransactionsRepo, TransactionParticipantsRepo, UsersRepo
from models.debts import Debt
from collections import deque


class DebtsService:
    """
    Всё, что связано с долгами:
    - полный пересчёт балансов по чату (на основе сырых транзакций и их участников),
    - оптимизация взаиморасчётов (минимальный набор переводов).
    """

    def __init__(
        self,
        session: Session,
        debts_repo: DebtsRepo,
        tx_repo: TransactionsRepo,
        parts_repo: TransactionParticipantsRepo,
        users_repo: UsersRepo,
    ) -> None:
        self.session = session
        self.debts = debts_repo
        self.txs = tx_repo
        self.parts = parts_repo
        self.users = users_repo

    # ---------- Пересчёт долгов ----------

    def rebuild(self, chat_id: int) -> List[Debt]:
        """
        Полный пересчёт таблицы `debts` для конкретного чата с нуля.
        Алгоритм:
          1) Собираем все транзакции чата.
          2) Для каждой смотрим её участников и их доли.
          3) Считаем агрегированный баланс каждого пользователя (положит./отрицат.).
          4) Перезаписываем таблицу debts для чата (upsert/обновление).
        """
        # 1) Инициализируем агрегатор
        balances: Dict[int, float] = {}

        # 2) Проходим по транзакциям чата
        tx_list = self.txs.list_by_chat(chat_id=chat_id, limit=10_000, offset=0)

        for tx in tx_list:
            # Создатель заплатил целиком -> ему должны на сумму долей
            creator_id = tx.creator_id
            if creator_id not in balances:
                balances[creator_id] = 0.0

            # Все участники этой транзакции
            parts = self.parts.list_by_transaction(transaction_id=tx.id)
            # Если участников нет — пропускаем
            if not parts:
                continue

            # Каждый участник уменьшает свой баланс на свою долю,
            # а баланс создателя увеличивается на эту долю
            for p in parts:
                balances[p.user_id] = balances.get(p.user_id, 0.0) - p.share_amount
                balances[creator_id] = balances.get(creator_id, 0.0) + p.share_amount

        # 3) Записываем агрегированные балансы в debts
        #    Правило: запись на пользователя должна быть одна (актуальный баланс).
        #    Если записи не было — создаём; если была — обновляем amount.
        result: List[Debt] = []
        for user_id, amount in balances.items():
            existing = self.debts.get_by_chat_user(chat_id=chat_id, user_id=user_id)
            if existing:
                updated = self.debts.update(id=existing.id, amount=amount)
                result.append(updated)
            else:
                created = self.debts.create(chat_id=chat_id, user_id=user_id, amount=amount)
                result.append(created)

        return result

    # ---------- Оптимизация взаиморасчётов ----------

    def optimize_settlements(self, chat_id: int) -> List[Tuple[int, int, float]]:
        """
        Возвращает минимальный набор переводов вида: (from_user_id, to_user_id, amount),
        чтобы все балансы стали ~0 (с точностью до копеек).
        Простой «жадный» алгоритм:
          - делим людей на должников (amount < 0) и кредиторов (amount > 0),
          - матчим самого «минусового» с самым «плюсовым» по очереди.
        """
        rows = self.debts.list_by_chat(chat_id=chat_id, limit=10_000, offset=0)

        # Очереди «кто должен» и «кому должны»
        debtors: deque[Tuple[int, float]] = deque()
        creditors: deque[Tuple[int, float]] = deque()

        for d in rows:
            if d.amount < -1e-6:
                debtors.append((d.user_id, -d.amount))  # храним положительную сумму долга
            elif d.amount > 1e-6:
                creditors.append((d.user_id, d.amount))

        settlements: List[Tuple[int, int, float]] = []

        while debtors and creditors:
            debtor_id, need = debtors[0]
            creditor_id, have = creditors[0]

            pay = min(need, have)  # сколько «свести» в этой паре
            settlements.append((debtor_id, creditor_id, round(pay, 2)))

            # уменьшили остатки
            need -= pay
            have -= pay

            debtors.popleft()
            creditors.popleft()

            if need > 1e-6:
                debtors.appendleft((debtor_id, need))
            if have > 1e-6:
                creditors.appendleft((creditor_id, have))

        return settlements
