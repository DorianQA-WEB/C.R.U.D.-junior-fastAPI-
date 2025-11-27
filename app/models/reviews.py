from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, Boolean, Numeric, DateTime
from decimal import Decimal
from sqlalchemy.orm import relationship, Mapped, mapped_column
from app.models.products import Product
from app.models.users import User
from app.database import Base


class Reviews(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("products.id"))
    comment: Mapped[str] = mapped_column(String(255), nullable=True)
    comment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    grade: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


    # Связи
    user: Mapped["User"] = relationship("User", back_populates="reviews")
    product: Mapped["Product"] = relationship("Product",
                                              back_populates="reviews",
                                              foreign_keys=[product_id])
