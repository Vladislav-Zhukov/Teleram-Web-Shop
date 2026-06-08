import { request } from "./http";

export async function changeStock(product_id: number, delta: number) {
  return request<{ id: number; stock: number; in_stock: boolean }>("/stock/change", {
    method: "POST",
    auth: true,
    body: JSON.stringify({ product_id, delta })
  });
}
