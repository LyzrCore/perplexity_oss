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
        sessionId: state.sessionId,  // Persist session across page reloads
      }),
      storage: {
        getItem: (name) => {
          // Use sessionStorage for sessionId (clears when browser closes)
          const str = window.sessionStorage.getItem(name);
          return str ? JSON.parse(str) : null;
        },
        setItem: (name, value) => {
          window.sessionStorage.setItem(name, JSON.stringify(value));
        },
        removeItem: (name) => {
          window.sessionStorage.removeItem(name);
        },
      },
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
    sessionId: state.sessionId,
    setSessionId: state.setSessionId,
    startDate: state.startDate,
    setStartDate: state.setStartDate,
    endDate: state.endDate,
    setEndDate: state.setEndDate,
    clearDateRange: state.clearDateRange,
  }));

export const useConfigStore = () =>
  useStore((state) => ({
    localMode: state.localMode,
    toggleLocalMode: state.toggleLocalMode,
    proMode: state.proMode,
    toggleProMode: state.toggleProMode,
  }));
