import asyncio
from aiogram import Bot, Dispatcher

import logging
logging.basicConfig(level=logging.INFO)

from app.settings import settings
from app.middlewares.error_middleware import ErrorMiddleware

# routers
from app.handlers.user_catalog import router as user_catalog_router
from app.handlers.user_cart_inline import router as user_cart_inline
from app.handlers.user_cart import router as user_cart_router
from app.handlers.user_checkout import router as user_checkout_router
from app.handlers.user_orders import router as user_orders_router
from app.handlers.user_help import router as user_help_order

from app.handlers.admin_orders import router as admin_orders_router
from app.handlers.admin_products_fsm import router as admin_products_fsm_router
from app.handlers.admin_products_manage import router as admin_products_manage_router
from app.handlers.admin_products import router as admin_products_router


async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(ErrorMiddleware())

    # user
    dp.include_router(user_cart_inline)
    dp.include_router(user_catalog_router)
    dp.include_router(user_cart_router)
    dp.include_router(user_checkout_router)
    dp.include_router(user_orders_router)
    dp.include_router(user_help_order)

    # admin
    dp.include_router(admin_orders_router)
    dp.include_router(admin_products_fsm_router)
    dp.include_router(admin_products_manage_router)
    dp.include_router(admin_products_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
