import { request } from "./http";

export type OrderItemIn = { product_id: number; quantity: number };

export type OrderItemOut = { product_id: number; quantity: number };
export type OrderOut = { id: number; user_id: number; status: string; items: OrderItemOut[] };
export type OrderPageOut = { items: OrderOut[]; total: number; limit: number; offset: number };

// Admin (human-friendly)
export type OrderItemAdminOut = {
  product_id: number;
  product_name: string;
  unit_price: number;
  quantity: number;
  line_total: number;
  image_url?: string | null;
};

export type OrderAdminOut = {
  id: number;
  user_id: number;
  user_email: string;
  status: string;
  created_at: string;
  total: number;
  items: OrderItemAdminOut[];
};

export type OrderAdminPageOut = { items: OrderAdminOut[]; total: number; limit: number; offset: number };

export async function createOrder(items: OrderItemIn[]) {
  return request<{ id: number; status: string }>("/orders/", {
    method: "POST",
    auth: true,
    body: JSON.stringify({ items }),
  });
}

export async function myOrders() {
  return request<any[]>("/orders/my", { auth: true });
}

export async function listOrdersAdmin(params: {
  limit: number;
  offset: number;
  status?: string;
  user_id?: number;
}) {
  const qs = new URLSearchParams({
    limit: String(params.limit),
    offset: String(params.offset),
  });
  if (params.status) qs.set("status", params.status);
  if (params.user_id) qs.set("user_id", String(params.user_id));

  return request<OrderAdminPageOut>(`/orders/?${qs.toString()}`, { auth: true });
}

export async function updateOrderStatus(orderId: number, status: string) {
  return request<OrderAdminOut>(`/orders/${orderId}/status`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify({ status }),
  });
}
