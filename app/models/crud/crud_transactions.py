from datetime import datetime
from sqlmodel import Session, select
from models.transactions import Transaction
from typing import Optional, List
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)


def create_transaction(session: Session, chat_id: int, creator_id: int, amount: float,
                       title: Optional[str] = None) -> Transaction:
    logger.info('Транзакция создана')
    transaction = Transaction(chat_id=chat_id, creator_id=creator_id, amount=amount, title=title)
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def get_transaction(session: Session, id: int) -> Optional[Transaction]:
    return session.get(Transaction, id)


def update_transaction(session: Session, id: int, amount: Optional[float] = None, title: Optional[str] = None) -> Optional[Transaction]:
    transaction = get_transaction(session, id)
    if not transaction:
        return None
    if amount is not None:
        transaction.amount = amount
    if title is not None:
        transaction.title = title
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def delete_transaction(session: Session, id: int, deleted_at: Optional[datetime] = None) -> bool:
    transaction = get_transaction(session, id)
    if not transaction:
        return False
    transaction.deleted_at = deleted_at or datetime.utcnow()
    session.delete(transaction)
    session.commit()
    return True


def list_transactions(session: Session) -> List[Transaction]:
    return session.exec(select(Transaction)).all()
