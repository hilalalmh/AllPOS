import { create } from "zustand";

import { login as apiLogin, fetchMe, logoutRemote } from "../services/auth";
import type { UserMe } from "../types";
import {
  clearAuth,
  getAccessToken,
  getRefreshToken,
  getUser,
  lockRefreshTokenWrites,
  setTokens,
  setUser,
  unlockRefreshTokenWrites,
} from "../utils/token";
import { useStoreProfileStore } from "./storeProfileStore";
import type { AxiosError } from "axios";

interface AuthState {
  user: UserMe | null;
  booting: boolean;
  login: (username: string, password: string) => Promise<void>;
  loadMe: () => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: (getUser() as UserMe | null) ?? null,
  booting: true,

  login: async (username, password) => {
    // Buka kembali penulisan token (setelah logout sebelumnya menguncinya).
    unlockRefreshTokenWrites();
    const res = await apiLogin(username, password);
    setTokens(res.access_token, res.refresh_token);
    try {
      const me = await fetchMe();
      setUser(me);
      set({ user: me });
    } catch (err) {
      clearAuth();
      set({ user: null, booting: false });
      throw err;
    }
  },

  loadMe: async () => {
    if (!getAccessToken()) {
      set({ booting: false });
      return;
    }
    try {
      const me = await fetchMe();
      setUser(me);
      set({ user: me, booting: false });
    } catch (err) {
      const isUnauthorized = (err as AxiosError)?.response?.status === 401;
      if (isUnauthorized) {
        clearAuth();
        set({ user: null, booting: false });
      } else {
        set({ booting: false });
      }
    }
  },

  logout: () => {
    // Kunci penulisan token dulu: refresh yang sedang berjalan (dari request
    // 401) tidak boleh mengembalikan token baru setelah clearAuth.
    lockRefreshTokenWrites();
    const refresh = getRefreshToken();
    if (refresh) {
      void logoutRemote(refresh).catch(() => {
        // Gagal revoke tidak menghalangi logout lokal.
      });
    }
    clearAuth();
    set({ user: null });
    useStoreProfileStore.getState().reset();
  },
}));