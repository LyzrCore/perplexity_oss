import { useEffect } from "react";
import { useChatStore } from "@/stores";
import { MessageRole } from "../generated";

/**
 * Hook to automatically scroll to the bottom when user sends a message
 */
export const useAutoScroll = (ref: React.RefObject<HTMLDivElement>) => {
  const { messages } = useChatStore();

  useEffect(() => {
    if (messages.at(-1)?.role === MessageRole.USER) {
      ref.current?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  }, [messages, ref]);
};