import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ThemeState {
  mode: 'light' | 'dark';
  toggle: () => void;
  setMode: (m: 'light' | 'dark') => void;
}

export const useThemeStore = create<ThemeState>()(
  persist(
    (set) => ({
      mode: 'dark',
      toggle: () => set((s) => ({ mode: s.mode === 'light' ? 'dark' : 'light' })),
      setMode: (m) => set({ mode: m }),
    }),
    { name: 'theme-storage' }
  )
);
