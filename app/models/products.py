from sqlalchemy import String, Boolean, Integer, Numeric, ForeignKey, text
from decimal import Decimal
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, TYPE_CHECKING
from app.database import Base
if TYPE_CHECKING:
    from app.models.categories import Category
    from app.models.reviews import Reviews
    from app.models.users import User


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(200), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id"), nullable=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Связь с категорией
    category : Mapped['Category'] = relationship(back_populates="products")
    # Связь с отзывами
    reviews: Mapped[List['Reviews']] = relationship("Reviews",
                                                    back_populates="product",
                                                    foreign_keys="Reviews.product_id")
    rating: Mapped[float | None] = mapped_column(Numeric(2, 1), nullable=True, server_default=text("0"))
    # Связь с продавцом
    seller: Mapped['User'] = relationship("User", back_populates="products")



