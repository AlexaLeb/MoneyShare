from sqlmodel import Session, select
from models.transaction_participants import TransactionParticipant
from typing import Optional, List
from logger.logging import get_logger

logger = get_logger(logger_name=__name__)


def create_participant(session: Session, transaction_id: int, user_id: int, share_amount: float,
                       tag: str = "без указания типа транзакции") -> TransactionParticipant:
    logger.info('Создан образ участника долга')
    participant = TransactionParticipant(transaction_id=transaction_id, user_id=user_id,
                                         share_amount=share_amount, tag=tag)
    session.add(participant)
    session.commit()
    session.refresh(participant)
    return participant


def get_participant(session: Session, id: int) -> Optional[TransactionParticipant]:
    return session.get(TransactionParticipant, id)


def update_participant(session: Session, id: int, share_amount: Optional[float] = None, tag: Optional[str] = None) -> Optional[TransactionParticipant]:
    participant = get_participant(session, id)
    if not participant:
        return None
    if share_amount is not None:
        participant.share_amount = share_amount
    if tag is not None:
        participant.tag = tag
    session.add(participant)
    session.commit()
    session.refresh(participant)
    return participant


def delete_participant(session: Session, id: int) -> bool:
    participant = get_participant(session, id)
    if not participant:
        return False
    session.delete(participant)
    session.commit()
    return True


def list_participants(session: Session) -> List[TransactionParticipant]:
    return session.exec(select(TransactionParticipant)).all()