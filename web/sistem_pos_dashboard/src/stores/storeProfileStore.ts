import { create } from "zustand";

import { fetchStoreProfile, updateStoreProfile } from "../services/storeProfile";
import type { StoreProfile } from "../types";

interface StoreProfileState {
  profile: StoreProfile | null;
  loading: boolean;
  error: string | null;
  load: () => Promise<void>;
  save: (payload: {
    store_name: string;
    address?: string | null;
    phone?: string | null;
    footer: string;
  }) => Promise<void>;
  reset: () => void;
}

let loadStartIf: Promise<void> | null = null;
// Naik saat reset/logout: load yang sudah berjalan dari sesi LAMA tidak boleh
// menulis profile-nya ke store setelah di-reset (mis. profile toko baru milik
// pengguna yang baru login) — hasil basi harus dibuang.
let storeGeneration = 0;

export const useStoreProfileStore = create<StoreProfileState>((set) => ({
  profile: null,
  loading: false,
  error: null,

  load: async () => {
    if (loadStartIf) {
      await loadStartIf;
      return;
    }
    const gen = ++storeGeneration;
    set({ loading: true, error: null });
    const run = (async () => {
      try {
        const profile = await fetchStoreProfile();
        if (gen === storeGeneration) set({ profile, loading: false });
      } catch (err) {
        if (gen === storeGeneration) {
          set({ error: (err as Error).message, loading: false });
        }
      } finally {
        if (gen === storeGeneration) loadStartIf = null;
      }
    })();
    loadStartIf = run;
    await run;
  },

  save: async (payload) => {
    set({ loading: true, error: null });
    try {
      const profile = await updateStoreProfile(payload);
      set({ profile, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false });
      throw err;
    }
  },

  reset: () => {
    storeGeneration++;
    loadStartIf = null;
    set({ profile: null, loading: false, error: null });
  },
}));
