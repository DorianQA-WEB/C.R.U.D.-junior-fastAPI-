from fastapi import FastAPI
from app.routers import categories
from app.routers import products
from app.routers import users
from app.routers import reviews
from app.routers import cart
from app.routers import orders
from fastapi.staticfiles import StaticFiles


# Создаём приложение FastAPI
app = FastAPI(
    title="FastAPI Интернет-магазин",
    version="0.1.0",
)

# Подключаем маршруты категорий
app.include_router(categories.router)
app.include_router(products.router)
app.include_router(users.router)
app.include_router(reviews.router)
app.include_router(cart.router)
app.include_router(orders.router)
app.mount("/media", StaticFiles(directory="media"), name='media')

# Корневой эндпоинт для проверки
@app.get("/")
async def root():
    """
    Корневой маршрут, подтверждающий, что API работает.
    """
    return {"message": "Добро пожаловать в API интернет-магазина!"}


