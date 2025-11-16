import React, { FC, useEffect, useState } from "react";
import { Streamdown } from "streamdown";
import rehypeRaw from "rehype-raw";
import { Skeleton } from "./ui/skeleton";
import { ChatMessage } from "../generated";

// Note: Streamdown handles streaming and incomplete markdown parsing internally,
// so we no longer need custom sentence splitting or streaming components

export interface MessageProps {
  /** The chat message to display */
  message: ChatMessage;
  /** Whether the message is currently being streamed */
  isStreaming?: boolean;
}

/**
 * Component for rendering citation links
 * Returns inline HTML to avoid breaking list and paragraph formatting
 */
const CitationText = ({ number, href }: { number: number; href: string }) => {
  return `<button style="display: inline; border: none; background: none; padding: 0; margin: 0 2px; cursor: pointer;" class="select-none no-underline"><a style="text-decoration: none;" href="${href}" target="_blank" rel="noopener noreferrer"><span style="display: inline-flex; position: relative; top: -0.1em;"><span style="display: inline-flex; align-items: center; justify-center: center; border-radius: 9999px; padding: 0 0.25rem; font-size: 0.6rem; font-family: monospace; min-width: 1rem; height: 1rem;" class="bg-muted text-muted-foreground">${number}</span></span></a></button>`;
};

// Streamdown handles streaming internally, so we don't need custom streaming components

export const MessageComponent: FC<MessageProps> = ({
  message,
  isStreaming = false,
}) => {
  const { content, sources } = message;
  const [parsedMessage, setParsedMessage] = useState<string>(content);

  useEffect(() => {
    // Match [number] but NOT when followed by (url) - that's a markdown link
    // Also ensure we're not matching list item numbers by checking for word boundaries
    const citationRegex = /(?<!\w)(\[\d+\])(?!\()/g;

    let newMessage = content;

    // First pass: Replace citation markers with HTML
    newMessage = newMessage.replace(citationRegex, (match) => {
      const number = match.slice(1, -1);
      const source = sources?.find(
        (source, idx) => idx + 1 === parseInt(number),
      );
      return CitationText({
        number: parseInt(number),
        href: source?.url ?? "",
      });
    });

    // Second pass: Clean up any malformed markdown patterns
    // Remove stray opening brackets that aren't followed by:
    // - A number and closing bracket: [1]
    // - Valid markdown link pattern: [text](url)
    newMessage = newMessage.replace(/\[(?!(\d+\]|[^\]]+\]\())/g, '');

    // Remove malformed link closures like ](url) without preceding text
    newMessage = newMessage.replace(/(?<![^\s])\]\((https?:\/\/[^\)]+)\)/g, '');

    setParsedMessage(newMessage);
  }, [content, sources]);

  return (
    <Streamdown
      // Enable parsing of incomplete markdown during streaming
      // This ensures markdown is rendered correctly even when tokens arrive incrementally
      parseIncompleteMarkdown={isStreaming}
      // Enable animations during streaming for smooth visual feedback
      isAnimating={isStreaming}
      // Preserve prose styling for consistency with existing design
      // The .prose classes from globals.css will style headings, lists, paragraphs, etc.
      className="prose dark:prose-invert max-w-none leading-relaxed break-words"
      // Note: Streamdown includes rehype-raw by default, but we explicitly pass it
      // to ensure citation HTML injection works reliably
      rehypePlugins={[rehypeRaw]}
    >
      {parsedMessage}
    </Streamdown>
  );
};

export const MessageComponentSkeleton = () => {
  return (
    <>
      <Skeleton className="w-full py-4 bg-card">
        <div className="flex flex-col gap-4">
          <Skeleton className="mx-5 h-2 bg-primary/30" />
          <Skeleton className="mx-5 h-2 bg-primary/30 mr-20" />
          <Skeleton className="mx-5 h-2 bg-primary/30 mr-40" />
        </div>
      </Skeleton>
    </>
  );
};
