import { useEffect, useMemo, useState } from "react";
import { listOrdersAdmin, updateOrderStatus, OrderAdminOut } from "../../api/orders";

const nextByStatus: Record<string, string[]> = {
  NEW: ["PAID", "CANCELED"],
  PAID: ["SHIPPED", "CANCELED"],
  SHIPPED: ["DELIVERED"],
  DELIVERED: [],
  CANCELED: [],
};

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

function formatMoney(v: number) {
  return new Intl.NumberFormat("ru-RU", { style: "currency", currency: "EUR" }).format(v);
}

function formatDt(s: string) {
  try {
    return new Date(s).toLocaleString("ru-RU");
  } catch {
    return s;
  }
}

export function OrdersAdmin() {
  const [items, setItems] = useState<OrderAdminOut[]>([]);
  const [total, setTotal] = useState(0);

  const [limit, setLimit] = useState(20);
  const [offset, setOffset] = useState(0);

  const [status, setStatus] = useState<string>("");
  const [userId, setUserId] = useState<string>("");

  const [open, setOpen] = useState<Record<number, boolean>>({});
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const page = useMemo(() => Math.floor(offset / limit) + 1, [offset, limit]);
  const pages = useMemo(() => Math.max(1, Math.ceil(total / limit)), [total, limit]);

  async function load(params?: { limit?: number; offset?: number }) {
    setLoading(true);
    setErr(null);
    try {
      const data = await listOrdersAdmin({
        limit: params?.limit ?? limit,
        offset: params?.offset ?? offset,
        status: status || undefined,
        user_id: userId ? Number(userId) : undefined,
      });
      setItems(data.items);
      setTotal(data.total);
      setLimit(data.limit);
      setOffset(data.offset);
    } catch (e: any) {
      setErr(e?.message || e?.error || "LOAD_FAILED");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load({ offset: 0 });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function changeStatus(orderId: number, to: string) {
    setErr(null);
    setLoading(true);
    try {
      await updateOrderStatus(orderId, to);
      await load();
    } catch (e: any) {
      setErr(e?.message || e?.error || "STATUS_UPDATE_FAILED");
    } finally {
      setLoading(false);
    }
  }

  function sumQty(o: OrderAdminOut) {
    return o.items.reduce((s, it) => s + it.quantity, 0);
  }

  return (
    <div className="card" style={{ background: "#0b1220" }}>
      <div className="row" style={{ alignItems: "center" }}>
        <h3 style={{ margin: 0 }}>Заказы</h3>
        <span className="spacer" />
        <button className="btn secondary" onClick={() => load()} disabled={loading}>
          {loading ? "Обновляем…" : "Обновить"}
        </button>
      </div>

      <div className="card" style={{ marginTop: 12, background: "#111827" }}>
        <div className="row" style={{ gap: 10, flexWrap: "wrap", alignItems: "center" }}>
          <select className="input" value={status} onChange={(e) => { setStatus(e.target.value); setOffset(0); }}>
            <option value="">Все статусы</option>
            {Object.keys(nextByStatus).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>

          <input
            className="input"
            value={userId}
            onChange={(e) => { setUserId(e.target.value); setOffset(0); }}
            placeholder="user_id (опционально)"
            inputMode="numeric"
          />

          <select
            className="input"
            value={String(limit)}
            onChange={(e) => {
              const l = Number(e.target.value);
              setLimit(l);
              setOffset(0);
              load({ limit: l, offset: 0 });
            }}
          >
            {[10, 20, 50, 100].map((l) => (
              <option key={l} value={l}>{l} / стр</option>
            ))}
          </select>

          <button className="btn" disabled={loading} onClick={() => load({ offset: 0 })}>
            Применить
          </button>

          <span className="spacer" />
          <span className="muted">
            Всего: <b>{total}</b> • Стр: <b>{page}</b>/<b>{pages}</b>
          </span>
        </div>
      </div>

      {err && <p style={{ color: "#fca5a5" }}>Ошибка: {err}</p>}

      <div style={{ display: "grid", gap: 10, marginTop: 12 }}>
        {items.map((o) => {
          const isOpen = !!open[o.id];
          const allowed = nextByStatus[o.status] ?? [];
          return (
            <div key={o.id} className="card" style={{ background: "#111827" }}>
              <div className="row" style={{ gap: 12, alignItems: "center" }}>
                <button
                  className="btn secondary"
                  onClick={() => setOpen((p) => ({ ...p, [o.id]: !isOpen }))}
                  title="Показать позиции"
                >
                  {isOpen ? "▾" : "▸"}
                </button>

                <b>Заказ #{o.id}</b>
                <span className="muted">{formatDt(o.created_at)}</span>

                <span className="spacer" />

                <span className="muted">
                  {o.user_email} <span className="muted">(id {o.user_id})</span>
                </span>

                <span className="spacer" />

                <span className="muted">
                  позиций: <b>{o.items.length}</b> • qty: <b>{sumQty(o)}</b>
                </span>

                <b style={{ marginLeft: 12 }}>{formatMoney(o.total)}</b>

                <span className="card" style={{ padding: "6px 10px", background: "#0b1220" }}>
                  <b>{o.status}</b>
                </span>
              </div>

              {allowed.length > 0 && (
                <div className="row" style={{ marginTop: 10, gap: 8, flexWrap: "wrap" }}>
                  <span className="muted">Сменить статус:</span>
                  {allowed.map((st) => (
                    <button key={st} className="btn" disabled={loading} onClick={() => changeStatus(o.id, st)}>
                      {st}
                    </button>
                  ))}
                </div>
              )}

              {isOpen && (
                <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
                  {o.items.map((it) => (
                    <div key={`${o.id}-${it.product_id}`} className="card" style={{ background: "#0b1220" }}>
                      <div className="row" style={{ gap: 12, alignItems: "center" }}>
                        {it.image_url ? (
                          <img
                            src={it.image_url.startsWith("http") ? it.image_url : `${API_URL}${it.image_url}`}
                            alt={it.product_name}
                            style={{ width: 54, height: 54, objectFit: "cover", borderRadius: 10 }}
                          />
                        ) : (
                          <div style={{ width: 54, height: 54, borderRadius: 10, background: "#111827" }} />
                        )}

                        <div style={{ display: "grid", gap: 2 }}>
                          <b>{it.product_name}</b>
                          <span className="muted">product_id: {it.product_id}</span>
                        </div>

                        <span className="spacer" />

                        <span className="muted">qty: <b>{it.quantity}</b></span>
                        <span className="muted">unit: <b>{formatMoney(it.unit_price)}</b></span>
                        <b>{formatMoney(it.line_total)}</b>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {!items.length && !loading && !err && <p className="muted">Пока заказов нет.</p>}
      </div>

      <div className="row" style={{ marginTop: 14, gap: 8, alignItems: "center" }}>
        <button
          className="btn secondary"
          disabled={offset <= 0 || loading}
          onClick={() => load({ offset: Math.max(0, offset - limit) })}
        >
          ←
        </button>
        <span className="muted">Страница {page} / {pages}</span>
        <button
          className="btn secondary"
          disabled={offset + limit >= total || loading}
          onClick={() => load({ offset: offset + limit })}
        >
          →
        </button>
        <span className="spacer" />
        <span className="muted">offset: {offset} • limit: {limit}</span>
      </div>
    </div>
  );
}
