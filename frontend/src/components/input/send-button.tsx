import { Button } from "../ui/button";
import { ArrowUp } from "lucide-react";

interface SendButtonProps {
  disabled: boolean;
}

/**
 * Send button component for chat input
 */
export const SendButton = ({ disabled }: SendButtonProps) => {
  return (
    <Button
      type="submit"
      variant="default"
      size="icon"
      className="rounded-full bg-tint aspect-square h-8 w-8 disabled:opacity-20 hover:bg-tint/80 overflow-hidden"
      disabled={disabled}
    >
      <ArrowUp size={20} />
    </Button>
  );
};