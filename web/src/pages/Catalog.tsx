import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { listProducts, Product } from "../api/products";
import { useAuth } from "../auth/useAuth";
import { createOrder } from "../api/orders";
import { loadCart, saveCart, saveCartMeta, setQty, CartMap } from "../cart/storage";
import { withApi } from "../api/http";

function formatMoney(v: number) {
  return new Intl.NumberFormat("ru-RU", { style: "currency", currency: "EUR" }).format(v);
}

export function Catalog() {
  const nav = useNavigate();
  const { user } = useAuth();

  // filters
  const [search, setSearch] = useState("");
  const [inStockOnly, setInStockOnly] = useState(false);
  const [minPrice, setMinPrice] = useState<string>("");
  const [maxPrice, setMaxPrice] = useState<string>("");

  // paging
  const [limit, setLimit] = useState(12);
  const [offset, setOffset] = useState(0);

  const [items, setItems] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [err, setErr] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const [cart, setCart] = useState<CartMap>(() => loadCart());

  useEffect(() => {
    saveCart(cart);
  }, [cart]);

  const cartCount = useMemo(() => Object.values(cart).reduce((s, v) => s + (Number(v) || 0), 0), [cart]);

  const cartTotal = useMemo(() => {
    const byId = new Map(items.map((p) => [p.id, p] as const));
    let sum = 0;
    for (const [pidStr, qty] of Object.entries(cart)) {
      const p = byId.get(Number(pidStr));
      if (!p) continue;
      sum += p.price * qty;
    }
    return sum;
  }, [cart, items]);

  useEffect(() => {
    // meta для Layout
    saveCartMeta({ count: cartCount, total: cartTotal });
  }, [cartCount, cartTotal]);

  async function load() {
    setErr(null);
    setLoading(true);
    try {
      const page = await listProducts({
        limit,
        offset,
        search: search.trim() || undefined,
        in_stock: inStockOnly ? true : undefined,
        min_price: minPrice ? Number(minPrice) : undefined,
        max_price: maxPrice ? Number(maxPrice) : undefined,
      });
      setItems(page.items);
      setTotal(page.total);
    } catch (e: any) {
      setErr(e?.error || "LOAD_FAILED");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [limit, offset]);

  // when filters change, reset to first page
  useEffect(() => {
    setOffset(0);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [search, inStockOnly, minPrice, maxPrice]);

  const page = Math.floor(offset / limit) + 1;
  const pages = Math.max(1, Math.ceil(total / limit));

  async function checkoutFromCatalog() {
    if (!user) {
      nav("/login");
      return;
    }
    const itemsToSend = Object.entries(cart).map(([pid, qty]) => ({
      product_id: Number(pid),
      quantity: Number(qty),
    })).filter((x) => x.quantity > 0);

    if (!itemsToSend.length) return;
    try {
      const res = await createOrder(itemsToSend);
      alert(`Заказ #${res.id} создан (status: ${res.status})`);
      setCart({});
      nav("/orders");
    } catch (e: any) {
      alert(`Ошибка оформления: ${e?.error || "CHECKOUT_FAILED"}`);
    }
  }

  return (
    <div className="card">
      <div className="row" style={{ alignItems: "center", gap: 12 }}>
        <h2 style={{ marginTop: 0, marginBottom: 0 }}>Каталог</h2>
        <span className="spacer" />
        {user && cartCount > 0 && (
          <button className="btn" onClick={checkoutFromCatalog}>
            Оформить • {cartCount} шт • {formatMoney(cartTotal)}
          </button>
        )}
      </div>

      <div className="card" style={{ marginTop: 12, background: "#0b1220" }}>
        <div className="row" style={{ gap: 10, flexWrap: "wrap" }}>
          <input
            placeholder="Поиск по названию..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ flex: 1, minWidth: 220 }}
          />

          <label className="muted" style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <input
              type="checkbox"
              checked={inStockOnly}
              onChange={(e) => setInStockOnly(e.target.checked)}
            />
            только в наличии
          </label>

          <input
            placeholder="min €"
            value={minPrice}
            onChange={(e) => setMinPrice(e.target.value)}
            style={{ width: 110 }}
          />
          <input
            placeholder="max €"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            style={{ width: 110 }}
          />

          <select value={limit} onChange={(e) => setLimit(Number(e.target.value))}>
            {[8, 12, 20, 50].map((x) => (
              <option key={x} value={x}>{x} / page</option>
            ))}
          </select>
        </div>
      </div>

      {err && <p style={{ color: "#fca5a5" }}>Ошибка: {err}</p>}

      <div className="row" style={{ marginTop: 12, alignItems: "center" }}>
        <span className="muted">Всего: {total}</span>
        <span className="spacer" />
        <div className="row" style={{ gap: 8 }}>
          <button className="btn secondary" disabled={page <= 1} onClick={() => setOffset(Math.max(0, offset - limit))}>
            ←
          </button>
          <span className="muted">{page} / {pages}</span>
          <button className="btn secondary" disabled={page >= pages} onClick={() => setOffset(offset + limit)}>
            →
          </button>
        </div>
      </div>

      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {loading && <p className="muted">Загрузка…</p>}

        {items.map((p) => {
          const qty = cart[p.id] ?? 0;
          const out = !p.in_stock || p.stock <= 0;
          const canInc = !out && qty < p.stock;

          return (
            <div key={p.id} className="card" style={{ background: "#0b1220" }}>
              <div className="row" style={{ gap: 12 }}>
                {p.primary_image_url ? (
                  <img
                    src={withApi(p.primary_image_url) ?? ""}
                    alt={p.name}
                    style={{ width: 72, height: 72, objectFit: "cover", borderRadius: 10 }}
                  />
                ) : (
                  <div style={{ width: 72, height: 72, borderRadius: 10, background: "#111827" }} />
                )}

                <div style={{ flex: 1 }}>
                  <div className="row">
                    <b>#{p.id} {p.name}</b>
                    <span className="spacer" />
                    <span>{formatMoney(p.price)}</span>
                  </div>
                  <div className="muted">{p.description}</div>
                  <div className="row" style={{ marginTop: 8, gap: 12 }}>
                    <span className="muted">stock: {p.stock}</span>
                    <span className="muted">{out ? "❌ out_of_stock" : "✅ in_stock"}</span>
                    <span className="spacer" />

                    {qty === 0 ? (
                      <button className="btn" disabled={out} onClick={() => setCart((prev) => setQty(prev, p.id, 1))}>
                        {out ? "Нет в наличии" : "В корзину"}
                      </button>
                    ) : (
                      <div className="row" style={{ gap: 8 }}>
                        <button className="btn secondary" onClick={() => setCart((prev) => setQty(prev, p.id, (prev[p.id] ?? 0) - 1))}>
                          −
                        </button>
                        <div className="card" style={{ padding: "8px 12px", minWidth: 54, textAlign: "center", background: "#111827" }}>
                          <b>{qty}</b>
                        </div>
                        <button className="btn secondary" disabled={!canInc} onClick={() => setCart((prev) => setQty(prev, p.id, (prev[p.id] ?? 0) + 1))}>
                          +
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}

        {!items.length && !err && !loading && <p className="muted">Пока пусто.</p>}
      </div>
    </div>
  );
}
