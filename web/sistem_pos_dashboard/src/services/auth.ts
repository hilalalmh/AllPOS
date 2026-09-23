import axios from "axios";
import { apiClient } from "./api";
import type { LoginResponse, UserMe } from "../types";

export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const { data } = await apiClient.post<LoginResponse>("/auth/login", {
    username,
    password,
  });
  return data;
}

export async function fetchMe(): Promise<UserMe> {
  const { data } = await apiClient.get<UserMe>("/auth/me");
  return data;
}

// Berjalan di luar apiClient untuk menghindari interceptor refresh;
// dipanggil saat logout untuk mencabut refresh token di server.
export function logoutRemote(refreshToken: string): Promise<void> {
  return axios
    .post("/api/v1/auth/logout", { refresh_token: refreshToken })
    .then(() => undefined);
}