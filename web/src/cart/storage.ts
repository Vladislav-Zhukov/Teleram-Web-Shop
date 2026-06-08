export const CART_KEY = "tgshop_cart_v1";
export const CART_META_KEY = "tgshop_cart_meta_v1";

export type CartMap = Record<number, number>;
export type CartMeta = { count: number; total: number };

export function loadCart(): CartMap {
  try {
    const raw = localStorage.getItem(CART_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw) as CartMap;
    const clean: CartMap = {};
    for (const [k, v] of Object.entries(parsed)) {
      const pid = Number(k);
      const qty = Number(v);
      if (Number.isFinite(pid) && Number.isFinite(qty) && qty > 0) clean[pid] = qty;
    }
    return clean;
  } catch {
    return {};
  }
}

export function saveCart(cart: CartMap) {
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
  window.dispatchEvent(new Event("cart:changed"));
}

export function loadCartMeta(): CartMeta {
  try {
    const raw = localStorage.getItem(CART_META_KEY);
    if (!raw) return { count: 0, total: 0 };
    const parsed = JSON.parse(raw) as CartMeta;
    return { count: Number(parsed?.count) || 0, total: Number(parsed?.total) || 0 };
  } catch {
    return { count: 0, total: 0 };
  }
}

export function saveCartMeta(meta: CartMeta) {
  localStorage.setItem(CART_META_KEY, JSON.stringify(meta));
  window.dispatchEvent(new Event("cart:changed"));
}

export function setQty(cart: CartMap, productId: number, qty: number): CartMap {
  const next = { ...cart };
  if (qty <= 0) delete next[productId];
  else next[productId] = qty;
  return next;
}
