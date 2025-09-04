from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import BigInteger


class Transaction(SQLModel, table=True):
    __tablename__ = "transactions"

    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="chats.id", sa_type=BigInteger)
    creator_id: int = Field(foreign_key="users.id", sa_type=BigInteger)
    amount: float
    title: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)

    chat: "Chat" = Relationship(back_populates="transactions")
    creator: "User" = Relationship(back_populates="transactions_created")
    # Каскад и delete-orphan прокидываем через sa_relationship_kwargs
    participants: List["TransactionParticipant"] = Relationship(
        back_populates="transaction",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "single_parent": True,
        },
    )

    def __repr__(self) -> str:
        return f"Transaction(id={self.id}, chat_id={self.chat_id}, creator_id={self.creator_id}, amount={self.amount})"
