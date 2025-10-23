import { useEffect, useRef } from "react";
import { useChatStore } from "@/stores";
import { MessageRole } from "../generated";

/**
 * Hook to automatically scroll to the bottom when user sends a message
 * Only scrolls if user is already near the bottom (to avoid interrupting reading)
 */
export const useAutoScroll = (ref: React.RefObject<HTMLDivElement>, isStreaming?: boolean) => {
  const { messages } = useChatStore();
  const previousMessageCount = useRef(0);
  const isUserNearBottom = useRef(true);

  // Track if user is near bottom of chat
  useEffect(() => {
    const handleScroll = () => {
      if (!ref.current) return;
      
      const container = ref.current.parentElement;
      if (!container) return;
      
      const { scrollTop, scrollHeight, clientHeight } = container;
      const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
      
      // Consider "near bottom" if within 100px of bottom
      isUserNearBottom.current = distanceFromBottom < 100;
    };

    const container = ref.current?.parentElement;
    if (container) {
      container.addEventListener('scroll', handleScroll);
      return () => container.removeEventListener('scroll', handleScroll);
    }
  }, [ref]);

  useEffect(() => {
    const currentMessageCount = messages.length;
    const lastMessage = messages.at(-1);
    
    // Only auto-scroll if:
    // 1. A new message was added (count increased)
    // 2. The last message is from the user (user sent a message)
    // 3. User is already near the bottom (not reading older messages)
    if (
      currentMessageCount > previousMessageCount.current &&
      lastMessage?.role === MessageRole.USER &&
      isUserNearBottom.current
    ) {
      ref.current?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
    
    previousMessageCount.current = currentMessageCount;
  }, [messages, ref]);

  // Auto-scroll when streaming starts (assistant begins responding)
  useEffect(() => {
    if (isStreaming && isUserNearBottom.current) {
      ref.current?.scrollIntoView({
        behavior: "smooth",
        block: "end",
      });
    }
  }, [isStreaming, ref]);
};