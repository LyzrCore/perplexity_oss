import { useEffect } from "react";

/**
 * Hook to automatically focus on an input element when component mounts
 */
export const useAutoFocus = (ref: React.RefObject<HTMLTextAreaElement>) => {
  useEffect(() => {
    ref.current?.focus();
  }, [ref]);
};