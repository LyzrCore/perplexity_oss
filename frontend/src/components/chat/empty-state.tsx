/**
 * Empty state component shown when no messages are present
 */
export const ChatEmptyState = ({ children }: { children: React.ReactNode }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-full w-full p-4 md:p-6 lg:p-8">
      <div className="flex flex-col items-center justify-center text-center space-y-6 mb-8 max-w-2xl animate-fade-in-up">
        <div className="space-y-4">
          <h1 className="text-3xl md:text-4xl lg:text-5xl font-bold text-foreground">
            Perplexity OSS
          </h1>
          <p className="text-base md:text-lg text-muted-foreground animate-fade-in" style={{ animationDelay: '200ms', animationFillMode: 'backwards' }}>
            Powered by <a href="https://lyzr.ai" target="_blank" className="text-primary font-semibold">Lyzr AI</a>
          </p>
        </div>
        <div className="space-y-2 animate-fade-in" style={{ animationDelay: '400ms', animationFillMode: 'backwards' }}>
          {/* <h2 className="text-xl md:text-2xl font-semibold text-foreground">
            Ask anything
          </h2> */}
          <p className="text-sm text-muted-foreground">
            Get instant answers with AI-powered search. Start a conversation to explore any topic.
          </p>
        </div>
      </div>
      <div className="w-full max-w-3xl animate-fade-in" style={{ animationDelay: '600ms', animationFillMode: 'backwards' }}>
        {children}
      </div>
    </div>
  );
};