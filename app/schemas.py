from pydantic import BaseModel, Field, ConfigDict, EmailStr
from decimal import Decimal


class CategoryCreate(BaseModel):
    """
    Модель для создания и обновления категории.
    Используется в POST и PUT запросах.
    """
    name: str = Field(..., min_length=3, max_length=55,
                      description="Название категории(от 3 до 55 символов)")
    parent_id: int | None = Field(None, description="ID родительской категории, если есть")


class CategoryResponse(BaseModel):
    """
    Модель для ответа с данными категории.
    Используется в GET-запросах.
    """
    id: int = Field(description="ID категории")
    name: str = Field(description="Название категории")
    parent_id: int | None = Field(None, description="ID родительской категории, если есть")
    is_active: bool = Field(description="Активна ли категория")

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    """
    Модель для создания и обновления товара.
    Используется в POST и PUT запросах.
    """
    name: str = Field(min_length=3, max_length=110,
                      description="Название товара (от 3 до 110 символов)")
    description: str | None = Field(None, max_length=555,
                                    description="Описание товара (не более 555 символов)")
    price: Decimal = Field(gt=0, description="Цена товара (больше 0)", decimal_places=2)
    image_url: str | None = Field(None, max_length=255, description="URL на изображение товара")
    stock: int = Field(gt=0, description="Количество товара на складе (0 или больше)")
    category_id: int = Field(description="ID категории, к которой относится товар")

class ProductResponse(BaseModel):
    """
    Модель для ответа с данными товара.
    Используется в GET-запросах.
    """
    id: int = Field(description="ID товара")
    name: str = Field(description="Название товара")
    description: str | None = Field(None, description="Описание товара")
    price: Decimal = Field(description="Цена товара", gt=0, decimal_places=2)
    image_url: str | None = Field(None, description="URL на изображение товара")
    stock: int = Field(description="Количество товара на складе")
    category_id: int = Field(description="ID категории, к которой относится товар")
    is_active: bool = Field(description="Активен ли товар")

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: EmailStr = Field(description="Email пользователя")
    password: str = Field(min_length=8, description="Пароль (минимум 8 символов)")
    role: str = Field(default="buyer", pattern="^(buyer|seller)$", description="Роль: 'buyer' или 'seller'")


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str
    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    product_id: int = Field(description="ID товара, к которому оставляется отзыв")
    comment: str | None = Field(None, max_length=555, description="Текст отзыва (не более 555 символов)")
    grade: int = Field(ge=1, le=5, description="Оценка товара (1-5)")

class ReviewResponse(BaseModel):

    id: int = Field(description="ID отзыва")
    product_id: int = Field(description="ID товара, к которому оставлен отзыв")
    comment: str | None = Field(None, description="Текст отзыва")
    grade: int = Field(description="Оценка товара")
    is_active: bool = Field(description="Активен ли отзыв")
    rating: float | None = None

    model_config = ConfigDict(from_attributes=True)

class ProductList(BaseModel):
    """
    Список пагинации для товаров.
    """
    items: list[ProductResponse] = Field(description="Товары для текущей страницы")
    total: int = Field(ge=0, description="Общее количество товаров")
    page: int = Field(ge=1, description="Текущая страница")
    page_size: int = Field(ge=1, description="Количество элементов на странице")

    model_config = ConfigDict(from_attributes=True) # Для чтения из ORM-объектов
