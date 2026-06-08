import { request } from "./http";

export type Product = {
  id: number;
  name: string;
  description: string;
  price: number;
  stock: number;
  in_stock: boolean;
  primary_image_url?: string | null;
  images?: ProductImage[];
};

export type ProductImage = {
  id: number;
  url: string;
  is_primary: boolean;
};

export type ProductPage = {
  items: Product[];
  total: number;
  limit: number;
  offset: number;
};

export async function listProducts(params?: {
  limit?: number;
  offset?: number;
  search?: string;
  min_price?: number;
  max_price?: number;
  in_stock?: boolean;
}) {
  const q = new URLSearchParams();
  if (params?.limit != null) q.set("limit", String(params.limit));
  if (params?.offset != null) q.set("offset", String(params.offset));
  if (params?.search) q.set("search", params.search);
  if (params?.min_price != null) q.set("min_price", String(params.min_price));
  if (params?.max_price != null) q.set("max_price", String(params.max_price));
  if (params?.in_stock != null) q.set("in_stock", params.in_stock ? "true" : "false");

  const suffix = q.toString() ? `?${q.toString()}` : "";
  return request<ProductPage>(`/products/${suffix}`);
}

export async function createProduct(data: {
  name: string; description?: string; price: number; stock?: number;
}) {
  return request<Product>("/products/", {
    method: "POST",
    auth: true,
    body: JSON.stringify(data)
  });
}

export async function getProduct(id: number) {
  return request<Product>(`/products/${id}`);
}

export type PatchProductIn = Partial<{
  name: string;
  description: string;
  price: number;
  stock: number;
  in_stock: boolean;
}>;

export async function patchProduct(id: number, data: PatchProductIn) {
  return request<{ ok: true }>(`/products/${id}`, {
    method: "PATCH",
    auth: true,
    body: JSON.stringify(data),
  });
}

export async function uploadProductImage(productId: number, file: File, makePrimary = true) {
  const fd = new FormData();
  fd.append("file", file);
  return request<ProductImage>(`/products/${productId}/images?make_primary=${makePrimary ? "true" : "false"}`, {
    method: "POST",
    auth: true,
    body: fd,
  });
}

export async function listProductImages(productId: number) {
  return request<ProductImage[]>(`/products/${productId}/images`, { method: "GET" });
}

export async function setPrimaryProductImage(productId: number, imageId: number) {
  return request<{ ok: true }>(`/products/${productId}/images/${imageId}/primary`, {
    method: "PATCH",
    auth: true,
  });
}

export async function deleteProductImage(productId: number, imageId: number) {
  return request<{ ok: true }>(`/products/${productId}/images/${imageId}`,
    {
      method: "DELETE",
      auth: true,
    }
  );
}

export async function deleteProduct(productId: number) {
  return request<{ ok: true }>(`/products/${productId}`, {
    method: "DELETE",
    auth: true,
  });
}
