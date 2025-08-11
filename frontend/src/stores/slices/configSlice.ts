import { env } from "@/env.mjs";
import { StateCreator } from "zustand";

type State = {
  localMode: boolean;
  proMode: boolean;
};

type Actions = {
  toggleLocalMode: () => void;
  toggleProMode: () => void;
};

export type ConfigStore = State & Actions;

export const createConfigSlice: StateCreator<
  ConfigStore,
  [],
  [],
  ConfigStore
> = (set) => ({
  localMode: false,
  proMode: false,
  toggleLocalMode: () =>
    set((state) => {
      // Local mode not applicable for Lyzr agents
      return { ...state, localMode: false };
    }),
  toggleProMode: () =>
    set((state) => {
      const proModeEnabled = env.NEXT_PUBLIC_PRO_MODE_ENABLED;
      if (!proModeEnabled) {
        return { ...state, proMode: false };
      }
      return { ...state, proMode: !state.proMode };
    }),
});
