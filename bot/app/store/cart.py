from dataclasses import dataclass, field


@dataclass
class Cart:
    items: dict[int, int] = field(default_factory=dict)  # product_id -> qty

    def add(self, product_id: int, qty: int = 1) -> None:
        current = int(self.items.get(product_id, 0))
        new_qty = current + int(qty)
        if new_qty <= 0:
            self.items.pop(product_id, None)
        else:
            self.items[product_id] = new_qty

    def clear(self) -> None:
        self.items.clear()


CARTS: dict[int, Cart] = {}


def get_cart(user_id: int) -> Cart:
    return CARTS.setdefault(user_id, Cart())
