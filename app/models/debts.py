from datetime import datetime
from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import BigInteger


class Debt(SQLModel, table=True):
    __tablename__ = "debts"

    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="chats.id", sa_type=BigInteger)
    user_id: int = Field(foreign_key="users.id", sa_type=BigInteger)
    amount: float = Field(default=0.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    chat: "Chat" = Relationship(back_populates="debts")
    user: "User" = Relationship(back_populates="debts")
    
    def __repr__(self) -> str:
        return f"Debt(id={self.id}, chat_id={self.chat_id}, user_id={self.user_id}, amount={self.amount})"
