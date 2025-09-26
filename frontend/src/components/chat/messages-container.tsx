import { forwardRef } from "react";
import { LoaderIcon } from "lucide-react";
import MessagesList from "../messages-list";
import { AskInput } from "../ask-input";
import { ChatMessage } from "../../generated";

interface MessagesContainerProps {
  messages: ChatMessage[];
  streamingMessage: ChatMessage | null;
  isStreamingMessage: boolean;
  isStreamingProSearch: boolean;
  isLoading: boolean;
  width: number;
  onSend: (message: string) => void;
  onRelatedQuestionSelect: (question: string) => void;
}

/**
 * Container component for displaying chat messages and input
 */
export const MessagesContainer = forwardRef<HTMLDivElement, MessagesContainerProps>(
  ({ 
    messages, 
    streamingMessage, 
    isStreamingMessage, 
    isStreamingProSearch,
    isLoading,
    width,
    onSend,
    onRelatedQuestionSelect
  }, messagesRef) => {
    if (isLoading) {
      return (
        <div className="w-full flex justify-center items-center">
          <LoaderIcon className="animate-spin w-8 h-8" />
        </div>
      );
    }

    return (
      <div ref={messagesRef} className="pt-10 w-full relative">
        <MessagesList
          messages={messages}
          streamingMessage={streamingMessage}
          isStreamingMessage={isStreamingMessage}
          isStreamingProSearch={isStreamingProSearch}
          onRelatedQuestionSelect={onRelatedQuestionSelect}
        />
        <div className="h-0" />
        <div
          className="bottom-12 fixed px-2 max-w-(--breakpoint-md) justify-center items-center md:px-2"
          style={{ width: `${width}px` }}
        >
          <AskInput isFollowingUp sendMessage={onSend} />
        </div>
      </div>
    );
  }
);

MessagesContainer.displayName = "MessagesContainer";