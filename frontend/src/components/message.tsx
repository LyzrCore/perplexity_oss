import React, { FC, useMemo, useEffect, useRef } from "react";
import { Streamdown } from "streamdown";
import rehypeRaw from "rehype-raw";
import { Skeleton } from "./ui/skeleton";
import { ChatMessage, SearchResult } from "../generated";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import { Logo } from "./search-results";

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
 * Note: data-citation-index is used to match with HoverCard wrappers
 */
const CitationText = ({ number, href, citationIndex }: { number: number; href: string; citationIndex: number }) => {
  return `<sup><span class="citation-link" data-citation-index="${citationIndex}"><span class="citation-badge">${number}</span></span></sup>`;
};

/**
 * Individual citation with hover card
 */
const CitationWithHover: FC<{ source: SearchResult; index: number }> = ({ source, index }) => {
  const { title, url, content } = source;
  const formattedUrl = new URL(url).hostname.split(".").slice(-2, -1)[0];

  return (
    <HoverCard openDelay={200} closeDelay={100}>
      <HoverCardTrigger asChild>
        {/* This span will be positioned over the citation badge */}
        <span
          className="citation-hover-trigger"
          data-citation-hover={index}
          style={{ display: 'none' }}
        />
      </HoverCardTrigger>
      <HoverCardContent className="w-80 py-2">
        <div className="flex justify-between space-x-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <div className="rounded-full overflow-hidden relative">
                <Logo url={url} />
              </div>
              <div className="text-xs text-muted-foreground truncate font-medium">
                {formattedUrl}
              </div>
            </div>
            <p className="text-sm font-medium">{title}</p>
            <span className="text-sm line-clamp-3 font-light text-foreground/90">
              {content}
            </span>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
};

export const MessageComponent: FC<MessageProps> = ({
  message,
  isStreaming = false,
}) => {
  const { content, sources } = message;
  const containerRef = useRef<HTMLDivElement>(null);

  // Use useMemo to process synchronously during render (not after like useEffect)
  const parsedMessage = useMemo(() => {
    // Match [number] but NOT when followed by (url) - that's a markdown link
    // Removed the word boundary check to allow citations like "fact[1]"
    const citationRegex = /\[(\d+)\](?!\()/g;

    let newMessage = content;

    // Create a placeholder map to protect citations during processing
    const citationPlaceholders: { [key: string]: string } = {};
    let placeholderIndex = 0;

    // Replace citation markers with placeholders AND store the HTML
    newMessage = newMessage.replace(citationRegex, (match, number) => {
      const sourceIndex = parseInt(number) - 1;
      const source = sources?.[sourceIndex];
      const placeholder = `___CITATION_${placeholderIndex}___`;
      citationPlaceholders[placeholder] = CitationText({
        number: parseInt(number),
        href: source?.url ?? "",
        citationIndex: sourceIndex,
      });
      placeholderIndex++;
      return placeholder;
    });

    // Restore citations from placeholders using a single regex replace
    // This ensures all citations are replaced reliably in one pass
    newMessage = newMessage.replace(/___CITATION_(\d+)___/g, (match) => {
      return citationPlaceholders[match] || match;
    });

    return newMessage;
  }, [content, sources]);

  // Attach hover card triggers to citation links after render
  useEffect(() => {
    if (!containerRef.current || !sources) return;

    const citationLinks = containerRef.current.querySelectorAll('.citation-link');

    citationLinks.forEach((link) => {
      const citationIndex = link.getAttribute('data-citation-index');
      if (!citationIndex) return;

      // Find corresponding hover trigger
      const hoverTrigger = containerRef.current?.querySelector(
        `[data-citation-hover="${citationIndex}"]`
      ) as HTMLElement;

      if (!hoverTrigger) return;

      // Forward mouse events from citation link to hover trigger
      const handleMouseEnter = () => {
        hoverTrigger.dispatchEvent(new MouseEvent('mouseenter', { bubbles: true }));
      };

      const handleMouseLeave = () => {
        hoverTrigger.dispatchEvent(new MouseEvent('mouseleave', { bubbles: true }));
      };

      const handleClick = (e: Event) => {
        e.preventDefault();
        e.stopPropagation();
        const source = sources[parseInt(citationIndex)];
        if (source?.url) {
          window.open(source.url, '_blank', 'noopener,noreferrer');
        }
      };

      link.addEventListener('mouseenter', handleMouseEnter);
      link.addEventListener('mouseleave', handleMouseLeave);
      link.addEventListener('click', handleClick);

      // Cleanup
      return () => {
        link.removeEventListener('mouseenter', handleMouseEnter);
        link.removeEventListener('mouseleave', handleMouseLeave);
        link.removeEventListener('click', handleClick);
      };
    });
  }, [parsedMessage, sources]);

  return (
    <div ref={containerRef} className="relative">
      <Streamdown
        // Enable parsing of incomplete markdown during streaming
        // This ensures markdown is rendered correctly even when tokens arrive incrementally
        parseIncompleteMarkdown={isStreaming}
        // Enable animations during streaming for smooth visual feedback
        isAnimating={isStreaming}
        // Preserve prose styling for consistency with existing design
        // The .prose classes from globals.css will style headings, lists, paragraphs, etc.
        className="prose dark:prose-invert max-w-none leading-relaxed break-words"
        // Pass rehypeRaw to enable HTML parsing
        rehypePlugins={[rehypeRaw]}
      >
        {parsedMessage}
      </Streamdown>

      {/* Hidden hover card triggers that will be activated by citation links */}
      {sources?.map((source, index) => (
        <CitationWithHover key={index} source={source} index={index} />
      ))}
    </div>
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
