"use client";

import { useEffect } from "react";
import { useChatStore } from "@/stores";

/**
 * Component that manages the animated gradient background based on conversation state
 * Shows gradient when no conversation is active, hides it when conversation starts
 */
export function GradientManager() {
  const { messages } = useChatStore();
  
  useEffect(() => {
    const hasConversation = messages.length > 0;
    
    if (hasConversation) {
      // Remove gradient when conversation starts
      document.body.classList.add('no-gradient-background');
      document.getElementById('white-gradient')?.classList.add('opacity-10');
    } else {
      // Show gradient when no conversation (remove override to use default)
      document.body.classList.remove('no-gradient-background');
      document.getElementById('white-gradient')?.classList.remove('opacity-10');
    }
    
    // Cleanup function to ensure proper state when component unmounts
    return () => {
      document.body.classList.remove('no-gradient-background');
    };
  }, [messages.length]);

  return null; // This component doesn't render anything
}
