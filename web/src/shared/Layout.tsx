import { Link, Outlet } from "react-router-dom";
import { useEffect, useMemo, useState } from "react";
import { useAuth } from "../auth/useAuth";
import { loadCartMeta } from "../cart/storage";
import { createTelegramLink, unlinkTelegram } from "../api/users";

export function Layout() {
  const { user, logout, refreshMe } = useAuth();
  const [cartMeta, setCartMeta] = useState(() => loadCartMeta());

  const [tg, setTg] = useState<{ code: string; expires_in: number } | null>(null);
  const [tgErr, setTgErr] = useState<string | null>(null);

  // Optional: if you inject it to the web container, you'll get a clickable deep link.
  const BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME || "";

  const tgLinkUrl = useMemo(() => {
    if (!BOT_USERNAME || !tg?.code) return "";
    return `https://t.me/${BOT_USERNAME}?start=${tg.code}`;
  }, [BOT_USERNAME, tg?.code]);

  useEffect(() => {
    const onChange = () => setCartMeta(loadCartMeta());
    window.addEventListener("cart:changed", onChange);
    return () => window.removeEventListener("cart:changed", onChange);
  }, []);

  useEffect(() => {
    setTg(null);
    setTgErr(null);
  }, [user?.id]);

  async function onTelegramLinkClick() {
    if (!user) return;
    try {
      setTgErr(null);
      const res = await createTelegramLink();
      setTg(res);

      if (BOT_USERNAME) {
        window.open(`https://t.me/${BOT_USERNAME}?start=${res.code}`, "_blank", "noopener,noreferrer");
      }
    } catch (e: any) {
      setTgErr(e?.error || e?.message || "Ошибка привязки Telegram");
    }
  }

  async function onTelegramUnlinkClick() {
    if (!user) return;
    try {
      setTgErr(null);
      await unlinkTelegram();
      await refreshMe();
      setTg(null);
    } catch (e: any) {
      setTgErr(e?.error || e?.message || "Ошибка отвязки Telegram");
    }
  }

  return (
    <div className="container">
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="row">
          <Link to="/" style={{ fontWeight: 700, textDecoration: "none" }}>TG Shop</Link>
          <Link to="/catalog">Каталог</Link>
          {user && <Link to="/orders">Заказы</Link>}
          {user?.is_admin && <Link to="/admin/products">Админка</Link>}
          <div className="spacer" />

          {user && (
            <span className="muted" title="Корзина хранится локально в браузере">
              🛒 {cartMeta.count} • {new Intl.NumberFormat("ru-RU", { style: "currency", currency: "EUR" }).format(cartMeta.total || 0)}
            </span>
          )}

          {user ? (
            <>
              <span className="muted" title={user.telegram_id ? "Telegram привязан" : "Telegram не привязан"}>
                {user.telegram_id ? "✅ Telegram привязан" : "❌ Telegram не привязан"}
              </span>

              {!user.telegram_id && (
                <button className="btn secondary" onClick={onTelegramLinkClick}>Привязать Telegram</button>
              )}

              {user.telegram_id && (
                <button className="btn secondary" onClick={onTelegramUnlinkClick}>Отвязать</button>
              )}

              <span className="muted">{user.email}</span>
              <button className="btn secondary" onClick={logout}>Выйти</button>
            </>
          ) : (
            <>
              <Link to="/login">Войти</Link>
              <Link to="/register">Регистрация</Link>
            </>
          )}
        </div>
      </div>

      {user && !user.telegram_id && (tgErr || tg) && (
        <div className="card" style={{ marginBottom: 12 }}>
          {tgErr && <div>❌ {tgErr}</div>}

          {tg && (
            <div>
              <div style={{ fontWeight: 700, marginBottom: 6 }}>Привязка Telegram</div>
              <div className="muted" style={{ marginBottom: 8 }}>
                Код действует: {tg.expires_in} сек.
              </div>

              {BOT_USERNAME && tgLinkUrl && (
                <>
                  <div style={{ marginBottom: 6 }}>Открой бота по ссылке:</div>
                  <div style={{ marginBottom: 10 }}>
                    <a href={tgLinkUrl} target="_blank" rel="noreferrer">
                      {tgLinkUrl}
                    </a>
                  </div>
                </>
              )}

              <div>
                Или отправь боту вручную:
                <div style={{ fontFamily: "monospace", marginTop: 6 }}>/start {tg.code}</div>
              </div>
            </div>
          )}
        </div>
      )}

      <Outlet />
    </div>
  );
}