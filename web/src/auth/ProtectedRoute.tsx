import { Navigate } from "react-router-dom";
import { useAuth } from "./useAuth";

export function ProtectedRoute({ children, requireAdmin = false }: { children: JSX.Element; requireAdmin?: boolean; }) {
  const { user, loading } = useAuth();

  if (loading) return <div className="card">Загрузка…</div>;
  if (!user) return <Navigate to="/login" replace />;

  if (requireAdmin && !user.is_admin) {
    return <div className="card">❌ Доступ запрещён (нужна роль admin).</div>;
  }
  return children;
}
