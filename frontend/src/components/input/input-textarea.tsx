import TextareaAutosize from "react-textarea-autosize";

interface InputTextareaProps {
  input: string;
  setInput: (input: string) => void;
  placeholder?: string;
}

/**
 * Reusable textarea component for chat input
 */
export const InputTextarea = ({ 
  input, 
  setInput, 
  placeholder = "Ask anything..." 
}: InputTextareaProps) => {
  return (
    <TextareaAutosize
      className="w-full bg-transparent text-md resize-none focus:outline-none p-2 z-20"
      placeholder={placeholder}
      onChange={(e) => setInput(e.target.value)}
      value={input}
    />
  );
};