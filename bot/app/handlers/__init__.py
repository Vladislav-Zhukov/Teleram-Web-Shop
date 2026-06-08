from .user_catalog import router as user_catalog
from .user_cart import router as user_cart
from .user_checkout import router as user_checkout
from .admin_products_fsm import router as admin_products_fsm
from .user_orders import router as user_orders
from .admin_orders import router as admin_orders

routers = [
    user_catalog,
    user_cart,
    user_checkout,
    admin_products_fsm,
    user_orders,
    admin_orders
]
