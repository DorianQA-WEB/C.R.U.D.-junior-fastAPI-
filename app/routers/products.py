from fastapi import APIRouter, status, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Category as CategoryModel
from app.schemas import ProductResponse
from sqlalchemy import select, update

from app.models.products import Product as ProductModel
from app.schemas import ProductResponse, ProductCreate
from app.db_depends import get_db


# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix='/products',
    tags=['products'],
)

@router.get('/products/', response_model=list[ProductResponse], status_code=status.HTTP_200_OK)
async def get_all_products(db: Session = Depends(get_db)):
    """
    Возвращает список всех товаров.
    """
    stmt = select(ProductModel).where(ProductModel.is_active == True,)
    products = db.scalars(stmt).all()
    return products

@router.get('/products/category/{category_id}', status_code=status.HTTP_200_OK, response_model=list[ProductResponse])
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по её ID.
    """
    stmt = select(CategoryModel).where(CategoryModel.id == category_id,)
    category = db.scalars(stmt).first()
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    stmt_products = select(ProductModel).where(ProductModel.category_id == category_id,
               ProductModel.is_active == True)
    products = db.scalars(stmt_products).all()
    return products


@router.get('/{product_id}', status_code=status.HTTP_200_OK, response_model=ProductResponse)
async def get_product(product_id: int, db: Session = Depends(get_db)):

    """
    Возвращает детальную информацию о товаре по его ID.
    """

    return {"message": f"Товар с ID {product_id} (заглушка)"}

@router.post('/products/', response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создаёт новый товар.
    """
    if product.category_id is None:
        stmt = select(ProductModel).where(ProductModel.id == product.category_id,
                                          ProductModel.is_active == True)
        parent = db.scalars(stmt).first()
        if parent is None:
            raise HTTPException(
                status_code=400,
                detail="Parent product not found"
            )

    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.put('/{product_id}')
async def update_product(product_id: int):
    """
    Обновляет информацию о товаре по его ID.
    """
    return {"message": f"Товар с ID {product_id} обновлён (заглушка)"}

@router.delete('/{product_id}')
async def delete_product(product_id: int):
    """
    Удаляет товар по его ID.
    """
    return {"message": f"Товар с ID {product_id} удалён (заглушка)"}
