import { useState } from "react";
import { useAuth } from "../auth/useAuth";
import { useNavigate } from "react-router-dom";

export function Register() {
  const { register } = useAuth();
  const nav = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr] = useState<string | null>(null);

  return (
    <div className="card">
      <h2 style={{ marginTop: 0 }}>Регистрация</h2>
      <div className="grid">
        <input className="input" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
        <input className="input" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="password" />
      </div>
      <div className="row" style={{ marginTop: 12 }}>
        <button
          className="btn"
          onClick={async () => {
            setErr(null);
            try {
              await register(email, password);
              nav("/catalog");
            } catch (e: any) {
              setErr(e?.error || "REGISTER_FAILED");
            }
          }}
        >
          Создать аккаунт
        </button>
      </div>
      {err && <p style={{ color: "#fca5a5" }}>Ошибка: {err}</p>}
    </div>
  );
}
