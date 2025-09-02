from sqlmodel import Session
from repositories import (
    UsersRepo,
    ChatsRepo,
    TransactionsRepo,
    TransactionParticipantsRepo,
    DebtsRepo,
)

from .users_service import UsersService
from .chats_service import ChatsService
from .transactions_service import TransactionsService
from .debts_service import DebtsService


class SplitService:
    """
    Фасад над маленькими сервисами.
    Никакой бизнес-логики — только создание зависимостей и «точка входа».
    """

    def __init__(self, session: Session) -> None:
        # Репозитории — однажды создаём на текущую сессию
        users_repo = UsersRepo(session)
        chats_repo = ChatsRepo(session)
        tx_repo = TransactionsRepo(session)
        parts_repo = TransactionParticipantsRepo(session)
        debts_repo = DebtsRepo(session)

        # Мелкие сервисы получают доступ к нужным репозиториям
        self.users = UsersService(session, users_repo)
        self.chats = ChatsService(session, chats_repo)
        self.transactions = TransactionsService(session, tx_repo, parts_repo, debts_repo)
        self.debts = DebtsService(session, debts_repo, tx_repo, parts_repo, users_repo)
