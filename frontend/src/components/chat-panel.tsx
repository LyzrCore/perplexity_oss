"use client";

import { useChat } from "@/hooks/chat";
import { useChatStore } from "@/stores";
import { useSearchParams } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { AskInput } from "./ask-input";
import { useChatThread } from "@/hooks/threads";
import { StarterQuestionsList } from "./starter-questions";
import { useAutoScroll } from "@/hooks/use-auto-scroll";
import { useAutoResize } from "@/hooks/use-auto-resize";
import { useAutoFocus } from "@/hooks/use-auto-focus";
import { ChatEmptyState } from "./chat/empty-state";
import { MessagesContainer } from "./chat/messages-container";

export const ChatPanel = ({ threadId }: { threadId?: number }) => {
  const searchParams = useSearchParams();
  const queryMessage = searchParams.get("q");
  const hasRun = useRef(false);

  const {
    handleSend,
    streamingMessage,
    isStreamingMessage,
    isStreamingProSearch,
  } = useChat();
  const { messages, setMessages, setThreadId } = useChatStore();
  const { data: thread, isLoading, error } = useChatThread(threadId);

  const [width, setWidth] = useState(0);
  const messagesRef = useRef<HTMLDivElement | null>(null);
  const messageBottomRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useAutoScroll(messageBottomRef);
  useAutoResize(messagesRef, setWidth);
  useAutoFocus(inputRef);

  useEffect(() => {
    if (queryMessage && !hasRun.current) {
      setThreadId(null);
      hasRun.current = true;
      handleSend(queryMessage);
    }
  }, [queryMessage, handleSend, setThreadId]);

  useEffect(() => {
    if (!thread) return;
    setThreadId(thread.thread_id);
    setMessages(thread.messages || []);
  }, [threadId, thread, setMessages, setThreadId]);

  useEffect(() => {
    if (messages.length == 0) {
      setThreadId(null);
    }
  }, [messages, setThreadId]);

  return (
    <>
      {messages.length > 0 || threadId ? (
        <>
          <MessagesContainer
            ref={messagesRef}
            messages={messages}
            streamingMessage={streamingMessage}
            isStreamingMessage={isStreamingMessage}
            isStreamingProSearch={isStreamingProSearch}
            isLoading={isLoading}
            width={width}
            onSend={handleSend}
            onRelatedQuestionSelect={handleSend}
          />
          <div ref={messageBottomRef} className="h-0" />
        </>
      ) : (
        <ChatEmptyState>
          <AskInput sendMessage={handleSend} />
          <div className="w-full flex flex-row justify-between space-y-2 pt-1">
            <StarterQuestionsList handleSend={handleSend} />
          </div>
        </ChatEmptyState>
      )}
    </>
  );
};
