from fastapi import APIRouter, status, Depends, HTTPException

from app.models import Category as CategoryModel
from sqlalchemy import select, update

from app.models.products import Product as ProductModel
from app.schemas import ProductResponse, ProductCreate

from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db

from app.models.users import User as UserModel
from app.auth import get_current_seller


# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix='/products',
    tags=['products'],
)

@router.get('/', response_model=list[ProductResponse], status_code=status.HTTP_200_OK)
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех товаров.
    """
    result = await db.scalars(select(ProductModel).where(ProductModel.is_active == True))
    return result.all()

@router.get('/category/{category_id}', status_code=status.HTTP_200_OK, response_model=list[ProductResponse])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    # Проверяем, существует ли активная категория
    result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == category_id,
                                    CategoryModel.is_active == True)
    )
    category = result.first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found or inactive")

    # Получаем активные товары в категории
    product_result = await db.scalars(
        select(ProductModel).where(ProductModel.category_id == category_id,
                                   ProductModel.is_active == True)
    )
    return product_result.all()


@router.get('/{product_id}', status_code=status.HTTP_200_OK, response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):

    """
    Возвращает детальную информацию о товаре по его ID.
    """
    # Проверяем, существует ли активный товар
    result = await db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    )
    product = result.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )

    # Проверяем, существует ли активная категория
    result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    )
    category = result.first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")
    return product

@router.post('/', response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
        product: ProductCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_seller)):
    """
    Создаёт новый товар, привязанный к текущему продавцу (только для 'seller').
    """
    # Проверяем, существует ли активная категория

    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    )
    if not category_result.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Category not found or inactive")

    # Создаём товар
    db_product = ProductModel(**product.model_dump(), seller_id=current_user.id)
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product) # Для получения id и is_active из базы
    return db_product

@router.put('/{product_id}', status_code=status.HTTP_200_OK, response_model=ProductResponse)
async def update_product(
        product_id: int, product: ProductCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_seller)):
    """
    Обновляет информацию о товаре по его ID.
    """
    # Проверяем, существует ли товар
    result = await db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    )
    db_product = result.first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    if db_product.seller_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only update your own products")
    # Проверяем, существует ли активная категория
    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    )
    if not category_result.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")

    # Обновляем товар
    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump())
    )
    await db.commit()
    await db.refresh(db_product)
    return db_product

@router.delete('/{product_id}', status_code=status.HTTP_200_OK)
async def delete_product(
        product_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_seller)):
    """
    Выполняет мягкое удаление товара, если он принадлежит текущему продавцу (только для 'seller').
    """
    # Проверяем, существует ли активный товар

    result = await db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    )
    product = result.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )
    if product.seller_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own products"
        )
    # Изменяем объект устанавив is_active=False и сохраняем
    await db.execute(
        update(ProductModel).where(ProductModel.id == product_id).values(is_active=False)
    )
    await db.commit()
    await db.refresh(product)
    return product
