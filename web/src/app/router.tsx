import { createBrowserRouter } from "react-router-dom";
import { Layout } from "../shared/Layout";
import { Home } from "../pages/Home";
import { Login } from "../pages/Login";
import { Register } from "../pages/Register";
import { Catalog } from "../pages/Catalog";
import { Orders } from "../pages/Orders";
import { ProtectedRoute } from "../auth/ProtectedRoute";
import { AdminLayout } from "../pages/admin/AdminLayout";
import { ProductsAdmin } from "../pages/admin/ProductsAdmin";
import { StockAdmin } from "../pages/admin/StockAdmin";
import { OrdersAdmin } from "../pages/admin/OrdersAdmin";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <Layout />,
    children: [
      { index: true, element: <Home /> },
      { path: "login", element: <Login /> },
      { path: "register", element: <Register /> },
      { path: "catalog", element: <Catalog /> },
      {
        path: "orders",
        element: (
          <ProtectedRoute>
            <Orders />
          </ProtectedRoute>
        )
      },
      {
        path: "admin",
        element: (
          <ProtectedRoute requireAdmin>
            <AdminLayout />
          </ProtectedRoute>
        ),
        children: [
          { path: "products", element: <ProductsAdmin /> },
          { path: "stock", element: <StockAdmin /> },
          { path: "orders", element: <OrdersAdmin /> }
        ]
      }
    ]
  }
]);
