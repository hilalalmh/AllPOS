import { create } from "zustand";

import { login as apiLogin, fetchMe, logoutRemote } from "../services/auth";
import type { UserMe } from "../types";
import {
  clearAuth,
  getAccessToken,
  getRefreshToken,
  getUser,
  setTokens,
  setUser,
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