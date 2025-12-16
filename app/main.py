from fastapi import FastAPI, BackgroundTasks
from app.routers import categories
from app.routers import products
from app.routers import users
from app.routers import reviews
from app.routers import cart
from app.routers import orders
from fastapi.staticfiles import StaticFiles
import time
from celery import Celery



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


celery = Celery(
    __name__,
    broker='redis://127.0.0.1:6379/0',
    backend='redis://127.0.0.1:6379/0',
    broker_connection_retry_on_startup=True,
)

def call_background_task(message):
    time.sleep(10)
    print(f'Background task: called!')
    print(message)


@app.get("/")
async def roots(message: str, background_tasks: BackgroundTasks):
    background_tasks.add_task(call_background_task, message)
    return {'message': 'Hello, world!'}


# Корневой эндпоинт для проверки
# @app.get("/")
# async def root():
#     """
#     Корневой маршрут, подтверждающий, что API работает.
#     """
#     return {"message": "Добро пожаловать в API интернет-магазина!"}
#

