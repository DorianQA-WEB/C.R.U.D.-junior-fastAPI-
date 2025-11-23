from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Category as CategoryModel
from sqlalchemy import select, update

from app.models.products import Product as ProductModel
from app.schemas import ProductResponse, ProductCreate
from app.db_depends import get_db


# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix='/products',
    tags=['products'],
)

@router.get('/', response_model=list[ProductResponse], status_code=status.HTTP_200_OK)
async def get_all_products(db: Session = Depends(get_db)):
    """
    Возвращает список всех товаров.
    """
    products = db.scalars(select(ProductModel).where(ProductModel.is_active == True)).all()
    return products

@router.get('/category/{category_id}', status_code=status.HTTP_200_OK, response_model=list[ProductResponse])
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    # Проверяем, существует ли активная категория
    category = db.scalars(
        select(CategoryModel).where(CategoryModel.id == category_id,
                                    CategoryModel.is_active == True)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found or inactive")

    # Получаем активные товары в категории
    products = db.scalars(
        select(ProductModel).where(ProductModel.category_id == category_id,
                                   ProductModel.is_active == True)
    ).all()
    return products


@router.get('/{product_id}', status_code=status.HTTP_200_OK, response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):

    """
    Возвращает детальную информацию о товаре по его ID.
    """
    # Проверяем, существует ли активный товар
    product = db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )

    # Проверяем, существует ли активная категория
    category = db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")
    return product

@router.post('/', response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создаёт новый товар.
    """
    # Проверяем, существует ли активная категория
    category = db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Category not found or inactive")

    # Создаём товар
    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put('/{product_id}', status_code=status.HTTP_200_OK, response_model=ProductResponse)
async def update_product(product_id: int, db: Session = Depends(get_db), product: ProductCreate = None):
    """
    Обновляет информацию о товаре по его ID.
    """
    # Проверяем, существует ли товар
    db_product = db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    ).first()
    if not db_product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    # Проверяем, существует ли активная категория
    category = db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)
    ).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Category not found or inactive")

    # Обновляем товар
    db.execute(
        update(ProductModel)
        .where(ProductModel.id == product_id)
        .values(**product.model_dump())
    )
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete('/{product_id}', status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, db: Session = Depends(get_db), ):
    """
    Удаляет товар по его ID.
    """
    # Проверяем, существует ли активный товар
    product = db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True)
    ).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )
    # Изменяем объект устанавив is_active=False и сохраняем
    product.is_active = False
    db.commit()
    return {"status": "success", "message": "Product marked as inactive"}
