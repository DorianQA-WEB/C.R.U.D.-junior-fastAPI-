from fastapi import APIRouter, status, Depends, HTTPException, Query

from app.models import Category as CategoryModel
from sqlalchemy import select, update, func, desc

from app.models.products import Product as ProductModel
from app.schemas import ProductResponse, ProductCreate, ProductList

from sqlalchemy.ext.asyncio import AsyncSession
from app.db_depends import get_async_db

from app.models.users import User as UserModel
from app.auth import get_current_seller


# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix='/products',
    tags=['products'],
)

@router.get('/', response_model=ProductList, status_code=status.HTTP_200_OK)
async def get_all_products(page: int = Query(1, ge=1),
                           page_size: int = Query(20, ge=1, le=100),
                           category_id: int | None = Query(None, description="ID категории для фильтрации"),
                           search: str | None = Query(None, min_length=1,
                                                      description="Поиск по названию/описанию товара"),
                           min_price: float | None = Query(
                            None, ge=0, description="Минимальная цена для товара"),
                           max_price: float | None = Query(
                               None, ge=0, description="Максимальная цена для товара"),
                           in_stock: bool | None = Query(
                               None, description="true — только товары в наличии, false — только без остатка"),
                           seller_id: int | None = Query(None, description="ID продавца для фильтрации"),
                           db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных товаров с поддержкой фильтров.
    """
    # Проверка логики min_price <= max_price
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price не может быть больше max_price"
        )

    # Формируем список фильтров
    filters = [ProductModel.is_active == True]
    if category_id is not None:
        filters.append(ProductModel.category_id == category_id)
    if search is not None:
        search_value = search.strip()
        if search_value:
            filters.append(func.lower(ProductModel.name).like(f'%{search_value.lower()}%'))
    if min_price is not None:
        filters.append(ProductModel.price >= min_price)
    if max_price is not None:
        filters.append(ProductModel.price <= max_price)
    if in_stock is not None:
        filters.append(ProductModel.stock > 0 if in_stock else ProductModel.stock == 0)
    if seller_id is not None:
        filters.append(ProductModel.seller_id == seller_id)

    # Базовый запрос total
    total_stmt = select(func.count()).select_from(ProductModel).where(*filters)

    rank_col = None
    if search:
        search_value = search.strip()
        if search_value:
            ts_query = func.websearch_to_tsquery('english', search_value)
            filters.append(ProductModel.tsv.op('@@')(ts_query))
            rank_col = func.ts_rank_cd(ProductModel.tsv, ts_query).label('rank')
            # total с учётом полнотекстового фильтра
            total_stmt = select(func.count()).select_from(ProductModel).where(*filters)


    total = await db.scalar(total_stmt) or 0

    # Основной запрос (если есть поиск — добавим ранг в выборку и сортировку)
    if rank_col is not None:
        products_stmt = (
            select(ProductModel, rank_col)
            .where(*filters)
            .order_by(desc(rank_col),ProductModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(products_stmt)
        rows = result.all()
        items = [row[0] for row in rows] # сами объекты
        # при желании можно вернуть ранг в ответе
        # ranks = [row.rank for row in rows]
    else:
        products_stmt = (
            select(ProductModel)
            .where(*filters)
            .order_by(ProductModel.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        items = (await db.scalars(products_stmt)).all()
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }

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
