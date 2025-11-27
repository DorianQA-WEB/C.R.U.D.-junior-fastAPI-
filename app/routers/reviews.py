from fastapi import APIRouter, HTTPException, status, Depends

from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db
from sqlalchemy import select, update, func
from app.models.reviews import Reviews as ReviewsModel
from app.auth import get_current_buyer, get_current_admin
from app.models.users import User as UserModel
from app.schemas import ReviewCreate, ReviewResponse
from app.models import Product as ProductModel


router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/", response_model=list[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_reviews(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех отзывов.
    """
    result = await db.scalars(select(ReviewsModel).where(ReviewsModel.id == reviews.id, ReviewsModel.is_active == True))
    return result.all()

@router.get("/product/{product_id}/reviews", response_model=list[ReviewResponse], status_code=status.HTTP_200_OK)
async def get_product_reviews(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список отзывов по конкретному продукту.
    """
    # Проверяем, существует ли активный продукт с указанным ID
    result = await db.scalars(select(ReviewsModel).where(ReviewsModel.product_id == product_id, ReviewsModel.is_active == True))
    product_reviews = result.all()
    if not product_reviews:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviews for the product not found or inactive")
    return product_reviews


@router.post("/", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
async def create_review(review_data: ReviewCreate,
                        db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_buyer)):
    """
    Добавляет отзыв на товар (только для 'buyer').
    Пересчитывает средний рейтинг товара после добавления отзыва.
    """
    # Проверяем, существует ли активный товар
    result = await db.scalars(select(ReviewsModel).where(ReviewsModel.product_id == review_data.product_id, ReviewsModel.is_active == True))
    product_reviews = result.first()
    if product_reviews.role != "buyer":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only buyers can leave reviews")
    if not product_reviews:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found or inactive")
    # Проверяем, что оценка в диапазоне 1–5
    if not 1 <= review_data.rating <= 5:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Rating must be between 1 and 5")
    # Создаём отзыв
    db_review = ReviewsModel(
        user_id=current_user.id,
        product_id=review_data.product_id,
        comment=review_data.comment,
        grade=review_data.grade,
        is_active=True
    )
    db.add(db_review)
    await db.commit()
    await db.refresh(db_review)
    # Пересчитываем средний рейтинг товара
    await recalculate_product_rating(db, review_data.product_id)
    return db_review


async def recalculate_product_rating(db: AsyncSession, product_id: int):
    """
    Пересчитывает средний рейтинг товара на основе активных отзывов.
    """
    result = await db.execute(
        select(func.avg(ReviewsModel.grade))
        .where(ReviewsModel.product_id == product_id, ReviewsModel.is_active == True)
    )
    avg_rating = result.scalar()

    new_rating = float(avg_rating) if avg_rating is not None else 0.0

    await db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(rating=new_rating)  # Убедитесь, что поле называется `rating`, а не `ratting`
    )
    await db.commit()

@router.delete("/{review_id}", status_code=status.HTTP_200_OK)
async def delete_review(review_id: int,
                        db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_admin)):
    """
    Мягко удаляет отзыв (только для админа). Пересчитывает рейтинг товара.
    """
    # Мягкое удаление
    # Находим отзыв
    result = await db.scalars(
        select(ReviewsModel).where(ReviewsModel.id == review_id, ReviewsModel.is_active == True)
    )
    review = result.first()
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found or already inactive")

    # Мягкое удаление
    await db.execute(
        update(ReviewsModel)
        .where(ReviewsModel.id == review_id)
        .values(is_active=False)
    )
    await db.commit()

    # Пересчёт рейтинга товара после удаления отзыва
    await recalculate_product_rating(db, review.product_id)

    return {"message": "Review deleted successfully"}