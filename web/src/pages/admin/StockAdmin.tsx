import { useState } from "react";
import { changeStock } from "../../api/stock";

export function StockAdmin() {
  const [pid, setPid] = useState("");
  const [delta, setDelta] = useState("1");
  const [msg, setMsg] = useState<string | null>(null);

  return (
    <div className="card" style={{ background: "#0b1220" }}>
      <h3 style={{ marginTop: 0 }}>Склад</h3>

      <div className="grid">
        <input className="input" value={pid} onChange={(e) => setPid(e.target.value)} placeholder="product_id" />
        <input className="input" value={delta} onChange={(e) => setDelta(e.target.value)} placeholder="delta (+/-)" />
      </div>

      <div className="row" style={{ marginTop: 12 }}>
        <button
          className="btn"
          onClick={async () => {
            setMsg(null);
            try {
              const res = await changeStock(Number(pid), Number(delta));
              setMsg(`OK: id=${res.id}, stock=${res.stock}, in_stock=${res.in_stock}`);
            } catch (e: any) {
              setMsg(`Ошибка: ${e?.error || "CHANGE_FAILED"}`);
            }
          }}
        >
          Изменить
        </button>
      </div>

      {msg && <p className="muted">{msg}</p>}
    </div>
  );
}
