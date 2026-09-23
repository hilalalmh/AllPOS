import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  clearAuth,
  getAccessToken,
  getRefreshToken,
  setTokens,
} from "../utils/token";

export const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

apiClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

interface RetryableConfig extends InternalAxiosRequestConfig {
  _retry?: boolean;
}

// Single-flight: semua request 401 menunggu proses refresh yang sama,
// agar tidak terjadi refresh token race / token berubah di tengah jalan.
let refreshPromise: Promise<{ access: string; refresh: string }> | null = null;

function refreshTokens(refreshToken: string) {
  if (!refreshPromise) {
    refreshPromise = axios
      .post<{ access_token: string; refresh_token: string }>(
        "/api/v1/auth/refresh",
        { refresh_token: refreshToken }
      )
      .then((res) => {
        const { access_token, refresh_token } = res.data;
        setTokens(access_token, refresh_token);
        return { access: access_token, refresh: refresh_token };
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryableConfig | undefined;
    if (!config || config._retry) {
      return Promise.reject(error);
    }

    const url = config.url ?? "";
    const isLoginCall = url.includes("/auth/login");
    const isRefreshCall = url.includes("/auth/refresh");
    if (error.response?.status !== 401 || isLoginCall || isRefreshCall) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      // Tanpa refresh token, sesi memang sudah habis — kabari UI agar
      // "login palsu" tidak menampilkan layar yang terlihat masuk.
      clearAuth();
      window.dispatchEvent(new Event("auth-expired"));
      return Promise.reject(error);
    }

    try {
      const tokens = await refreshTokens(refreshToken);
      // Retry aman hanya untuk request idempotent atau pembuatan transaksi
      // (dilindungi local_ref di sisi server). Request POST lain tidak boleh
      // diulang otomatis agar efek samping tidak berlipat.
      const method = (config.method ?? "get").toUpperCase();
      const isIdempotent =
        method === "GET" || method === "HEAD" || method === "OPTIONS";
      const isTxCreate = method === "POST" && url.includes("/transactions");
      if (!isIdempotent && !isTxCreate) {
        return Promise.reject(error);
      }
      config._retry = true;
      config.headers.Authorization = `Bearer ${tokens.access}`;
      return apiClient(config);
    } catch {
      clearAuth();
      window.dispatchEvent(new Event("auth-expired"));
      return Promise.reject(error);
    }
  }
);