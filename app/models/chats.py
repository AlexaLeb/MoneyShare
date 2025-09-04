from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import BigInteger


class Chat(SQLModel, table=True):
    __tablename__ = "chats"

    id: int = Field(primary_key=True, index=True, sa_type=BigInteger)  # Telegram chat_id
    title: Optional[str] = Field(default=None)

    transactions: List["Transaction"] = Relationship(back_populates="chat")
    debts: List["Debt"] = Relationship(back_populates="chat")

    def __repr__(self) -> str:
        return f"Chat(id={self.id}, title={self.title})"
