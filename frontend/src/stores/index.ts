import { create } from "zustand";
import { persist } from "zustand/middleware";
import { ConfigStore, createConfigSlice } from "./slices/configSlice";
import { createMessageSlice, ChatStore } from "./slices/messageSlice";

type StoreState = ChatStore & ConfigStore;

const useStore = create<StoreState>()(
  persist(
    (...a) => ({
      ...createMessageSlice(...a),
      ...createConfigSlice(...a),
    }),
    {
      name: "store",
      partialize: (state) => ({
        localMode: state.localMode,
        proMode: state.proMode,
      }),
      migrate: (persistedState: any, version: number) => {
        // Remove any old model references from persisted state
        if (persistedState.model) {
          delete persistedState.model;
        }
        return persistedState;
      },
      version: 1,
    },
  ),
);

export const useChatStore = () =>
  useStore((state) => ({
    messages: state.messages,
    addMessage: state.addMessage,
    setMessages: state.setMessages,
    threadId: state.threadId,
    setThreadId: state.setThreadId,
  }));

export const useConfigStore = () =>
  useStore((state) => ({
    localMode: state.localMode,
    toggleLocalMode: state.toggleLocalMode,
    proMode: state.proMode,
    toggleProMode: state.toggleProMode,
  }));
