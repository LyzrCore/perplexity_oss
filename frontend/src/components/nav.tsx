"use client";

import Link from "next/link";
import { ModeToggle } from "./mode-toggle";
import { useTheme } from "next-themes";
import { Button } from "./ui/button";
import { HistoryIcon, PlusIcon } from "lucide-react";
import { useChatStore } from "@/stores";
import { useRouter } from "next/navigation";

const NewChatButton = () => {
  return (
    <Button variant="secondary" size="sm" onClick={() => (location.href = "/")}>
      <PlusIcon className="w-4 h-4" />
      <span className="block">&nbsp;&nbsp;New</span>
    </Button>
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
              className="w-10 h-10 rounded-lg bg-gradient-to-br 
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
        <ModeToggle />
      </div>
    </header>
  );
}
