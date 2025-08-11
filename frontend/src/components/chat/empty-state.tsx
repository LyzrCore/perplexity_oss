/**
 * Empty state component shown when no messages are present
 */
export const ChatEmptyState = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="w-full flex flex-col justify-center items-center">
      <div className="flex flex-col items-center justify-center mb-8 text-center">
        <h1 className="text-4xl font-bold mb-2">Perplexity OSS</h1>
        <p className="text-lg text-muted-foreground mb-4">
          Powered by <span className="text-purple-600 font-medium">Lyzr AI</span>
        </p>
        <span className="text-2xl">Ask anything</span>
      </div>
      {children}
    </div>
  );
};