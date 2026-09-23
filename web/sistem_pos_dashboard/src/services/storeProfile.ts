import { apiClient } from "./api";
import type { StoreProfile } from "../types";

export interface StoreProfileUpdatePayload {
  store_name?: string;
  address?: string | null;
  phone?: string | null;
  footer?: string;
}

export async function fetchStoreProfile(): Promise<StoreProfile> {
  const { data } = await apiClient.get<StoreProfile>("/store-profile");
  return data;
}

export async function updateStoreProfile(
  payload: StoreProfileUpdatePayload
): Promise<StoreProfile> {
  const { data } = await apiClient.put<StoreProfile>("/store-profile", payload);
  return data;
}
