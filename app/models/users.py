from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import BigInteger


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: int = Field(primary_key=True, index=True, sa_type=BigInteger)  # Telegram ID
    username: Optional[str] = Field(default=None)
    first_name: Optional[str] = Field(default=None)

    transactions_created: List["Transaction"] = Relationship(back_populates="creator")
    transaction_participants: List["TransactionParticipant"] = Relationship(back_populates="user")
    debts: List["Debt"] = Relationship(back_populates="user")

    def __repr__(self) -> str:
        return f"User(id={self.id}, username={self.username}, first_name={self.first_name})"
