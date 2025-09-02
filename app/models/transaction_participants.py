from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from sqlalchemy import Column, Integer, ForeignKey


class TransactionParticipant(SQLModel, table=True):
    __tablename__ = "transaction_participants"

    id: Optional[int] = Field(default=None, primary_key=True)
    transaction_id: int = Field(
        sa_column=Column(
            Integer,
            ForeignKey("transactions.id", ondelete="CASCADE"),
            nullable=False,
        )
    )
    user_id: int = Field(foreign_key="users.id")
    share_amount: float
    tag: str = Field(default="без указания типа транзакции")

    transaction: Optional["Transaction"] = Relationship(
        back_populates="participants",
        sa_relationship_kwargs={"passive_deletes": True}
    )
    user: "User" = Relationship(back_populates="transaction_participants")

    def __repr__(self) -> str:
        return f"TransactionParticipant(id={self.id}, user_id={self.user_id}, share_amount={self.share_amount})"
