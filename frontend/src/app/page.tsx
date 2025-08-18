"use client";

import { ChatPanel } from "@/components/chat-panel";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { USER_KEY } from "@/lib/constants";
import { Suspense, useEffect, useState } from "react";

const LoginPrompt = () => {
  const handleLogin = () => {
    // Remove any query parameters and refresh the page
    const currentUrl = new URL(window.location.href);
    const cleanUrl = `${currentUrl.origin}${currentUrl.pathname}`;
    window.location.href = cleanUrl;
  };

  return (
    <div className="flex flex-col items-center justify-center h-full space-y-4">
      <div className="text-center">
        <h1 className="text-2xl font-bold mb-2">Welcome to Perplexity OSS</h1>
        <p className="text-muted-foreground mb-6">
          Please authenticate with your Lyzr account to continue
        </p>
        <Button onClick={handleLogin} size="lg">
          Login with Lyzr
        </Button>
      </div>
    </div>
  );
};

export default function Home() {
  const { isAuthenticated, isLoading, userId } = useAuth();
  const [hasCredentials, setHasCredentials] = useState(false);

  // Check if we have both user_id and api_key
  useEffect(() => {
    const apiKey = localStorage.getItem(USER_KEY);
    setHasCredentials(Boolean(userId && apiKey));
  }, [userId]);

  // Show loading while auth is initializing or credentials are not ready
  if (isLoading || (isAuthenticated && !hasCredentials)) {
    return (
      <div className="h-screen">
        <div className="flex grow h-full mx-auto max-w-screen-md px-4 md:px-8">
          <div className="flex items-center justify-center w-full">
            <div className="animate-pulse text-center">
              <div className="w-12 h-12 bg-muted rounded-full mx-auto mb-4"></div>
              <p className="text-muted-foreground">
                {isLoading ? "Loading..." : "Preparing your session..."}
              </p>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="h-screen">
        <div className="flex grow h-full mx-auto max-w-screen-md px-4 md:px-8">
          <LoginPrompt />
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen">
      <div className="flex grow h-full mx-auto max-w-screen-md px-4 md:px-8">
        <Suspense>
          <ChatPanel />
        </Suspense>
      </div>
    </div>
  );
}
