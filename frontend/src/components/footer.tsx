import Link from "next/link";
import { Button } from "./ui/button";
import { SiGithub, SiLinkedin } from "react-icons/si";
import { Globe } from "lucide-react";

export function Footer() {
  return (
    <footer className="w-full flex fixed bottom-0 right-0 p-1 z-50 bg-gradient-to-t from-background/95 to-transparent">
      <div className="px-1 w-full flex flex-row justify-start space-x-1">
        <Button variant="ghost" size="icon" className="hover:bg-transparent">
          <Link href="https://lyzr.ai" target="_blank">
            <Globe size={16} />
          </Link>
        </Button>
        <Button variant="ghost" size="icon" className="hover:bg-transparent">
          <Link
            href="https://github.com/LyzrCore/perplexity_oss"
            target="_blank"
          >
            <SiGithub size={16} />
          </Link>
        </Button>
        <Button variant="ghost" size="icon" className="hover:bg-transparent">
          <Link
            href="https://www.linkedin.com/company/lyzr-platform"
            target="_blank"
          >
            <SiLinkedin size={16} />
          </Link>
        </Button>
      </div>
    </footer>
  );
}
