import { create, StateCreator } from "zustand";
import { ChatMessage } from "../../generated";

type State = {
  threadId: number | null;
  sessionId: string | null;
  messages: ChatMessage[];
  startDate: string | null;
  endDate: string | null;
};

type Actions = {
  addMessage: (message: ChatMessage) => void;
  setThreadId: (threadId: number | null) => void;
  setSessionId: (sessionId: string | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setStartDate: (startDate: string | null) => void;
  setEndDate: (endDate: string | null) => void;
  clearDateRange: () => void;
};

export type ChatStore = State & Actions;

export const createMessageSlice: StateCreator<ChatStore, [], [], ChatStore> = (
  set,
) => ({
  threadId: null,
  sessionId: null,
  messages: [],
  startDate: null,
  endDate: null,
  addMessage: (message: ChatMessage) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setThreadId: (threadId: number | null) => set((state) => ({ threadId })),
  setSessionId: (sessionId: string | null) => set((state) => ({ sessionId })),
  setMessages: (messages: ChatMessage[]) => set((state) => ({ messages })),
  setStartDate: (startDate: string | null) => set((state) => ({ startDate })),
  setEndDate: (endDate: string | null) => set((state) => ({ endDate })),
  clearDateRange: () => set((state) => ({ startDate: null, endDate: null })),
});
