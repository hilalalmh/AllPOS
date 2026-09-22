import { apiClient } from "./api";
import type {
  BestSellerList,
  DashboardSummary,
  SalesPoint,
} from "../types";

export async function fetchSummary(
  start_date?: string,
  end_date?: string
): Promise<DashboardSummary> {
  const { data } = await apiClient.get<DashboardSummary>("/dashboard/summary", {
    params: start_date && end_date ? { start_date, end_date } : undefined,
  });
  return data;
}

export async function fetchSales(
  start_date?: string,
  end_date?: string,
  group_by: "day" | "month" = "day"
): Promise<SalesPoint[]> {
  const { data } = await apiClient.get<SalesPoint[]>("/dashboard/sales", {
    params: { start_date, end_date, group_by },
  });
  return data;
}

export async function fetchBestSellers(
  start_date?: string,
  end_date?: string,
  limit = 5
): Promise<BestSellerList> {
  const { data } = await apiClient.get<BestSellerList>("/dashboard/best-sellers", {
    params: start_date && end_date ? { start_date, end_date, limit } : { limit },
  });
  return data;
}