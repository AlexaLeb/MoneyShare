from datetime import datetime
from sqlmodel import Session, select
from models.debts import Debt
from typing import Optional, List
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)


def create_debt(session: Session, chat_id: int, user_id: int, amount: float = 0.0) -> Debt:
    logger.info('Создан долг')
    debt = Debt(chat_id=chat_id, user_id=user_id, amount=amount)
    session.add(debt)
    session.commit()
    session.refresh(debt)
    return debt


def get_debt(session: Session, id: int) -> Optional[Debt]:
    return session.get(Debt, id)


def update_debt(session: Session, id: int, amount: Optional[float] = None) -> Optional[Debt]:
    debt = get_debt(session, id)
    if not debt:
        return None
    if amount is not None:
        debt.amount = amount
        debt.updated_at = datetime.utcnow()
    session.add(debt)
    session.commit()
    session.refresh(debt)
    return debt


def delete_debt(session: Session, id: int) -> bool:
    debt = get_debt(session, id)
    if not debt:
        return False
    session.delete(debt)
    session.commit()
    return True


def list_debts(session: Session) -> List[Debt]:
    return session.exec(select(Debt)).all()