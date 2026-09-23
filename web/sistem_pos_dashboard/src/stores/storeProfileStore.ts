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

let loadStarted = false;

export const useStoreProfileStore = create<StoreProfileState>((set) => ({
  profile: null,
  loading: false,
  error: null,

  load: async () => {
    if (loadStarted) return;
    loadStarted = true;
    set({ loading: true, error: null });
    try {
      const profile = await fetchStoreProfile();
      set({ profile, loading: false });
    } catch (err) {
      set({ error: (err as Error).message, loading: false });
    }
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
    loadStarted = false;
    set({ profile: null, loading: false, error: null });
  },
}));
