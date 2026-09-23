import axios, {
  type AxiosError,
  type InternalAxiosRequestConfig,
} from "axios";

import {
  clearAuth,
  getAccessToken,
  getAuthGeneration,
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

// Notifikasi "auth-expired" cukup sekali per sesi (direset saat login/logout)
// agar banyak request 401 yang berbarengan tidak men-dispatch berulang kali.
let authExpiredDispatched = false;

/** Reset state refresh + flag notifikasi. Panggil saat login/logout. */
export function resetAuthRefreshState(): void {
  refreshPromise = null;
  authExpiredDispatched = false;
}

function notifyAuthExpired(): void {
  if (authExpiredDispatched) return;
  authExpiredDispatched = true;
  window.dispatchEvent(new Event("auth-expired"));
}

function refreshTokens(refresh: { token: string; authGeneration: number }) {
  if (!refreshPromise) {
    refreshPromise = axios
      .post<{ access_token: string; refresh_token: string }>(
        "/api/v1/auth/refresh",
        { refresh_token: refresh.token }
      )
      .then((res) => {
        const { access_token, refresh_token } = res.data;
        // Refresh yang mulai di generasi sesi LAMA (mis. sebelum login ulang)
        // dibuang: hasilnya tidak boleh menimpali token sesi yang lebih baru.
        if (getAuthGeneration() !== refresh.authGeneration) {
          throw Object.assign(new Error("stale refresh"), {
            stale: true,
          } as { stale: boolean });
        }
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
      notifyAuthExpired();
      return Promise.reject(error);
    }

    try {
      const tokens = await refreshTokens({
        token: refreshToken,
        authGeneration: getAuthGeneration(),
      });
      // Retry aman hanya untuk request idempotent atau pembuatan transaksi
      // (dilindungi local_ref di sisi server). Request POST lain — termasuk
      // POST /transactions/{id}/cancel yang non-idempoten — tidak boleh
      // diulang otomatis agar efek samping tidak berlipat.
      const method = (config.method ?? "get").toUpperCase();
      const isIdempotent =
        method === "GET" ||
        method === "HEAD" ||
        method === "OPTIONS" ||
        method === "PUT" ||
        method === "PATCH" ||
        method === "DELETE";
      const isTxCreate = method === "POST" && url === "/transactions";
      if (!isIdempotent && !isTxCreate) {
        return Promise.reject(error);
      }
      config._retry = true;
      config.headers.Authorization = `Bearer ${tokens.access}`;
      return apiClient(config);
    } catch (refreshErr) {
      // Logout paksa HANYA bila refresh benar-benar ditolak (HTTP 401,
      // token invalid). Gangguan jaringan/5xx bukan akhir sesi — pengguna
      // tidak boleh kehilangan login karena koneksi yang bermasalah.
      if ((refreshErr as AxiosError)?.response?.status === 401) {
        clearAuth();
        notifyAuthExpired();
      }
      return Promise.reject(error);
    }
  }
);