import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/toaster";
import Providers from "@/providers";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { GeistSans } from "geist/font/sans";
import { JetBrains_Mono as Mono } from "next/font/google";
import { cn } from "@/lib/utils";
import { Analytics } from "@vercel/analytics/react";
import { Navbar } from "@/components/nav";
import { Footer } from "@/components/footer";

const mono = Mono({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-mono",
});

const title = "Perplexity OSS - Powered by Lyzr Agent Studio";
const description = "Open-source AI-powered search engine built with Lyzr Agents.";

export const metadata: Metadata = {
  metadataBase: new URL("https://studio.lyzr.ai/"),
  title,
  description,
  openGraph: {
    title,
    description,
  },
  twitter: {
    title,
    description,
    card: "summary_large_image",
    creator: "@lyzrai",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <>
      <html lang="en" suppressHydrationWarning>
        <body
          className={cn("antialiased", GeistSans.className, mono.className)}
        >
          <Providers>
            <ThemeProvider
              attribute="class"
              defaultTheme="dark"
              enableSystem
              disableTransitionOnChange
            >
              <Navbar />
              {children}
              <Toaster />
              <Footer />
              <Analytics />
            </ThemeProvider>
          </Providers>
        </body>
      </html>
    </>
  );
}
