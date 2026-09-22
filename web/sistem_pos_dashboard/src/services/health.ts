import { apiClient } from "./api";

export interface HealthResponse {
  status: string;
  database: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await apiClient.get<HealthResponse>("/health");
  return data;
}