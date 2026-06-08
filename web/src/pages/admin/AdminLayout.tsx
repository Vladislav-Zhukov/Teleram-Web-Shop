import { Link, Outlet } from "react-router-dom";

export function AdminLayout() {
  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>Админка</h2>
      <div className="row" style={{ marginBottom: 12 }}>
        <Link className="btn secondary" to="/admin/products">Товары</Link>
        <Link className="btn secondary" to="/admin/stock">Склад</Link>
        <Link className="btn secondary" to="/admin/orders">Заказы</Link>
      </div>
      <Outlet />
    </div>
  );
}
