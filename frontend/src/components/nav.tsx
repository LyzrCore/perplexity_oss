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
    <Button variant="secondary" size="sm" onClick={() => (location.href = "/")}>
      <PlusIcon className="w-4 h-4" />
      <span className="block">&nbsp;&nbsp;New</span>
    </Button>
  );
};

const AuthSection = () => {
  const { isAuthenticated, isLoading, user, logout } = useAuth();

  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <div className="animate-pulse bg-muted rounded w-8 h-8"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm">
          <UserIcon className="w-4 h-4 mr-2" />
          Login
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-muted-foreground">
        {user?.email}
      </span>
      <Button variant="ghost" size="sm" onClick={logout}>
        <LogOutIcon className="w-4 h-4" />
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
    <header className="w-full flex fixed p-1 z-50 px-2 bg-background/95 justify-between items-center">
      <div className="flex items-center gap-2">
        <Link href="/" passHref onClick={() => (location.href = "/")}>
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-lg bg-linear-to-br 
     from-purple-500 to-purple-600 flex items-center justify-center text-white font-bold
     text-lg"
            >
              P
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-bold text-purple-600">
                Perplexity OSS
              </span>
              <span className="text-xs text-muted-foreground">
                powered by Lyzr AI
              </span>
            </div>
          </div>
        </Link>
        {!onHomePage && <NewChatButton />}
      </div>
      <div className="flex items-center gap-4">
        <AuthSection />
        <ModeToggle />
      </div>
    </header>
  );
}
