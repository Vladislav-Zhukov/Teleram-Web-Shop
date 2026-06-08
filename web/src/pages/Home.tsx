import { Link } from "react-router-dom";

export function Home() {
  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>Главная</h2>
      <p className="muted">
        Это веб-клиент к FastAPI backend. Бот и сайт используют один и тот же API.
      </p>
      <div className="row">
        <Link className="btn" to="/catalog">Открыть каталог</Link>
        <Link className="btn secondary" to="/login">Войти</Link>
      </div>
    </div>
  );
}
