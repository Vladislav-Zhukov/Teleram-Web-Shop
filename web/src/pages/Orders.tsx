import { useEffect, useState } from "react";
import { myOrders } from "../api/orders";

export function Orders() {
  const [items, setItems] = useState<any[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      setErr(null);
      try {
        setItems(await myOrders());
      } catch (e: any) {
        setErr(e?.error || "LOAD_FAILED");
      }
    })();
  }, []);

  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>Мои заказы</h2>
      {err && <p style={{ color: "#fca5a5" }}>Ошибка: {err}</p>}
      <div style={{ display: "grid", gap: 10 }}>
        {items.map((o) => (
          <div key={o.id} className="card" style={{ background: "#0b1220" }}>
            <div className="row">
              <b>Заказ #{o.id}</b>
              <span className="spacer" />
              <span className="muted">{o.status}</span>
            </div>
            <div className="muted" style={{ marginTop: 6 }}>
              {o.items?.map((it: any) => (
                <div key={`${it.product_id}:${it.quantity}`}>• product_id={it.product_id} × {it.quantity}</div>
              ))}
            </div>
          </div>
        ))}
        {!items.length && !err && <p className="muted">Пока нет заказов.</p>}
      </div>
    </div>
  );
}
