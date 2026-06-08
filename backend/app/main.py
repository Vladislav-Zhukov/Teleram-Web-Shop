import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.logging_conf import setup_logging
from app.settings import settings
from app.api.routers import auth, products, orders, stock, users
from app.api.errors import register_exception_handlers
from app.integrations.redis import create_redis, close_redis
from app.api.routers import admin_product_images


setup_logging()

app = FastAPI(title="TG Shop API")

os.makedirs(settings.MEDIA_DIR, exist_ok=True)
app.mount(settings.MEDIA_URL_PREFIX, StaticFiles(directory=settings.MEDIA_DIR), name="media")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list() or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)
app.include_router(stock.router)
app.include_router(orders.router)
app.include_router(admin_product_images.router)

register_exception_handlers(app)


@app.on_event("startup")
async def _startup() -> None:
    app.state.redis = create_redis()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await close_redis(getattr(app.state, "redis", None))

@app.get("/health")
async def health():
    return {"status": "ok"}
