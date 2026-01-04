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
from app.database import DATABASE_URL
from contextlib import asynccontextmanager

# Глобальные переменные для хранения ресурсов
db_connection_pool = DATABASE_URL
ml_model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Код ДО yield: Выполняется при СТАРТЕ приложения
    print("Приложение запускается: Инициализация ресурсов...")
    global db_connection_pool
    global ml_model

    try:
    # Инициализация пула соединений с базой данных
        db_connection_pool = {'status': 'connected','connection': 'ok'}
        print(f"Пул соединений с базой данных {db_connection_pool} инициализирован.")
    # Загрузка большой модели машинного обучения
        ml_model = {'name': "AI-ML-Model", 'status': "loaded"}
        print(f"Модель машинного обучения {ml_model} загружена.")

    # Здесь можно запустить фоновые задачи, инициализировать кэши и т.д.
        print("Ресурсы успешно инициализированы.")
    # yield - это разделитель!
    # Код после yield будет выполнен только при остановке приложения.
        yield

    except Exception as e:
        print(f"Ошибка при инициализации ресурсов: {e}")
        # В случае ошибки при запуске, приложение не будет запущено
        raise # Перевыбрасываем исключение, чтобы сервер не стартовал

    finally:
    # Код ПОСЛЕ yield (или в finally блока): Выполняется при ОСТАНОВКЕ приложения
        print("Приложение останавливается: Очистка ресурсов...")
    if db_connection_pool:
    # Закрытие пула соединений с БД
        db_connection_pool = None
        print("Пул соединений с базой данных закрыт.")
    if ml_model:
        ml_model = None
        print("Модель машинного обучения выгружена.")





# Создаём приложение FastAPI
app = FastAPI(
    title="FastAPI Интернет-магазин",
    version="0.1.0",
    lifespan=lifespan
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
async def read_root(message: str, background_tasks: BackgroundTasks):
    # Теперь мы можем использовать глобальные ресурсы
    background_tasks.add_task(call_background_task, message)
    if db_connection_pool and ml_model:
        return {
            "massage": "Hello, from fastapi!",
            "db_status": db_connection_pool["status"],
            "ml_status": ml_model["name"]
        }
    return {"message": "Resources not available!"}


# Корневой эндпоинт для проверки
# @app.get("/")
# async def root():
#     """
#     Корневой маршрут, подтверждающий, что API работает.
#     """
#     return {"message": "Добро пожаловать в API интернет-магазина!"}
#

