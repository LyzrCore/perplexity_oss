import { useState } from "react";
import ProToggle from "./pro-toggle";
import { InputTextarea } from "./input/input-textarea";
import { SendButton } from "./input/send-button";

/**
 * Initial input component
 */
const InputBar = ({
  input,
  setInput,
}: {
  input: string;
  setInput: (input: string) => void;
}) => {
  return (
    <div className="w-full flex flex-col rounded-md focus:outline-none px-2 py-1 bg-card border-2 z-20">
      <div className="w-full max-h-[200px] overflow-y-auto">
        <InputTextarea input={input} setInput={setInput} />
      </div>
      <div className="flex justify-end">
        <div className="flex items-center gap-2">
          <ProToggle />
          <SendButton disabled={input.trim().length < 5} />
        </div>
      </div>
    </div>
  );
};

/**
 * Follow-up input component (compact version)
 */
const FollowingUpInput = ({
  input,
  setInput,
}: {
  input: string;
  setInput: (input: string) => void;
}) => {
  return (
    <div className="w-full flex flex-row rounded-full border bg-card px-4 py-2 shadow-md transition-shadow hover:shadow-lg items-center gap-3">
      <div className="w-full">
        <InputTextarea input={input} setInput={setInput} />
      </div>
      <div className="flex items-center gap-2 flex-shrink-0">
        <ProToggle />
        <SendButton disabled={input.trim().length < 5} />
      </div>
    </div>
  );
};

interface AskInputProps {
  sendMessage: (message: string) => void;
  isFollowingUp?: boolean;
}

const MIN_INPUT_LENGTH = 5;

/**
 * Main chat input component with form handling
 */
export const AskInput = ({
  sendMessage,
  isFollowingUp = false,
}: AskInputProps) => {
  const [input, setInput] = useState("");
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim().length < MIN_INPUT_LENGTH) return;
    sendMessage(input);
    setInput("");
  };
  
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (input.trim().length < MIN_INPUT_LENGTH) return;
      sendMessage(input);
      setInput("");
    }
  };
  
  return (
    <form
      className="w-full overflow-hidden"
      onSubmit={handleSubmit}
      onKeyDown={handleKeyDown}
    >
      {isFollowingUp ? (
        <FollowingUpInput input={input} setInput={setInput} />
      ) : (
        <InputBar input={input} setInput={setInput} />
      )}
    </form>
  );
};
