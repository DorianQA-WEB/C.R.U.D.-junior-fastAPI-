from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import TYPE_CHECKING, List
from app.database import Base
if TYPE_CHECKING:
    from app.models.reviews import Reviews
    from app.models.products import Product

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    role: Mapped[str] = mapped_column(String, default='buyer') # "buyer" or "seller"

    products: Mapped[list["Product"]] = relationship("Product", back_populates="seller")
    reviews: Mapped[list["Reviews"]] = relationship("Reviews", back_populates="user")
