import { create, StateCreator } from "zustand";
import { ChatMessage } from "../../generated";

type State = {
  threadId: number | null;
  sessionId: string | null;
  messages: ChatMessage[];
};

type Actions = {
  addMessage: (message: ChatMessage) => void;
  setThreadId: (threadId: number | null) => void;
  setSessionId: (sessionId: string | null) => void;
  setMessages: (messages: ChatMessage[]) => void;
};

export type ChatStore = State & Actions;

export const createMessageSlice: StateCreator<ChatStore, [], [], ChatStore> = (
  set,
) => ({
  threadId: null,
  sessionId: null,
  messages: [],
  addMessage: (message: ChatMessage) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setThreadId: (threadId: number | null) => set((state) => ({ threadId })),
  setSessionId: (sessionId: string | null) => set((state) => ({ sessionId })),
  setMessages: (messages: ChatMessage[]) => set((state) => ({ messages })),
});
