import { apiClient } from "./api";
import type { Product, ProductList } from "../types";

export interface ProductQuery {
  q?: string;
  category_id?: number;
  include_inactive?: boolean;
  page?: number;
  page_size?: number;
}

export async function fetchProducts(params: ProductQuery): Promise<ProductList> {
  const { data } = await apiClient.get<ProductList>("/products", { params });
  return data;
}

export interface ProductInput {
  category_id: number;
  name: string;
  description?: string | null;
  sku?: string | null;
  price: number;
  is_active: boolean;
}

function toFormData(payload: ProductInput, image?: File | null): FormData {
  const form = new FormData();
  form.append("category_id", String(payload.category_id));
  form.append("name", payload.name);
  form.append("price", String(payload.price));
  form.append("is_active", String(payload.is_active));
  if (payload.description) form.append("description", payload.description);
  if (payload.sku) form.append("sku", payload.sku);
  if (image) form.append("image", image);
  return form;
}

export async function createProduct(
  payload: ProductInput,
  image?: File | null
): Promise<Product> {
  const { data } = await apiClient.post<Product>(
    "/products",
    toFormData(payload, image),
    { headers: { "Content-Type": "multipart/form-data" } }
  );
  return data;
}

export async function updateProduct(
  id: number,
  payload: ProductInput
): Promise<Product> {
  const { data } = await apiClient.put<Product>(`/products/${id}`, payload);
  return data;
}

export async function deleteProduct(id: number): Promise<void> {
  await apiClient.delete(`/products/${id}`);
}