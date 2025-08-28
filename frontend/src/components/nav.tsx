"use client";

import Link from "next/link";
import { ModeToggle } from "./mode-toggle";
import { useTheme } from "next-themes";
import { Button } from "./ui/button";
import { HistoryIcon, PlusIcon, LogOutIcon, UserIcon } from "lucide-react";
import { useChatStore } from "@/stores";
import { useAuth } from "@/contexts/AuthContext";
import { useRouter } from "next/navigation";

const NewChatButton = () => {
  return (
    <Button 
      variant="outline" 
      size="sm" 
      onClick={() => (location.href = "/")}
      className="gap-2"
    >
      <PlusIcon className="h-4 w-4" />
      <span className="hidden sm:inline">New Chat</span>
    </Button>
  );
};

const AuthSection = () => {
  const { isAuthenticated, isLoading, user, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <div className="animate-pulse bg-muted rounded-full w-8 h-8"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <Button variant="outline" size="sm" className="gap-2">
        <UserIcon className="h-4 w-4" />
        <span className="hidden sm:inline">Login</span>
      </Button>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground font-medium hidden md:inline">
        {user?.email}
      </span>
      <Button variant="ghost" size="sm" onClick={logout} className="gap-2">
        <LogOutIcon className="h-4 w-4" />
        <span className="hidden sm:inline">Logout</span>
      </Button>
    </div>
  );
};

export function Navbar() {
  const router = useRouter();
  const { theme } = useTheme();
  const { messages } = useChatStore();

  const onHomePage = messages.length === 0;

  return (
    <header className="fixed top-0 left-0 right-0 z-40 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 animate-slide-in-right">
      <div className="flex h-16 items-center justify-between px-4 md:px-6 lg:px-8">
        <div className="flex items-center gap-4">
          <Link href="/" onClick={() => (location.href = "/")} className="flex items-center gap-3 hover:opacity-80 transition-all duration-200 ">
            <div className="w-8 h-8 md:w-10 md:h-10 rounded-lg bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white font-bold text-sm md:text-lg shadow-lg">
              <img src="/lyzr.png" alt="Perplexity OSS" />
            </div>
            <div className="hidden sm:flex flex-col">
              <span className="text-lg md:text-xl font-bold text-foreground">
                Perplexity OSS
              </span>
              <span className="text-xs text-muted-foreground">
                powered by Lyzr AI
              </span>
            </div>
          </Link>
          {!onHomePage && (
            <div className="animate-fade-in" style={{ animationDelay: '300ms', animationFillMode: 'backwards' }}>
              <NewChatButton />
            </div>
          )}
        </div>
        <div className="flex items-center gap-2 md:gap-4 animate-fade-in" style={{ animationDelay: '200ms', animationFillMode: 'backwards' }}>
          <AuthSection />
          <ModeToggle />
        </div>
      </div>
    </header>
  );
}
