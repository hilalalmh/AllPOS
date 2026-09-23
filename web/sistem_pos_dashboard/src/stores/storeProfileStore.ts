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

export const useStoreProfileStore = create<StoreProfileState>((set) => ({
  profile: null,
  loading: false,
  error: null,

  load: async () => {
    if (loadStartIf) {
      await loadStartIf;
      return;
    }
    set({ loading: true, error: null });
    const run = (async () => {
      try {
        const profile = await fetchStoreProfile();
        set({ profile, loading: false });
      } catch (err) {
        set({ error: (err as Error).message, loading: false });
      } finally {
        loadStartIf = null;
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
    set({ profile: null, loading: false, error: null });
  },
}));
