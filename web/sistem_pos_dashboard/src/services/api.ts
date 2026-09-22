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

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetryableConfig | undefined;
    if (!config || config._retry) {
      return Promise.reject(error);
    }

    const isRefreshCall = (config.url ?? "").includes("/auth/refresh");
    if (error.response?.status !== 401 || isRefreshCall) {
      return Promise.reject(error);
    }

    const refreshToken = getRefreshToken();
    if (!refreshToken) {
      clearAuth();
      return Promise.reject(error);
    }

    try {
      const { data } = await axios.post<{
        access_token: string;
        refresh_token: string;
      }>("/api/v1/auth/refresh", { refresh_token: refreshToken });
      setTokens(data.access_token, data.refresh_token);
      config._retry = true;
      config.headers.Authorization = `Bearer ${data.access_token}`;
      return apiClient(config);
    } catch {
      clearAuth();
      window.dispatchEvent(new Event("auth-expired"));
      return Promise.reject(error);
    }
  }
);