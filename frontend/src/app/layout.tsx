import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/toaster";
import Providers from "@/providers";
import type { Metadata } from "next";
import "./globals.css";
import { GeistSans } from "geist/font/sans";
import { JetBrains_Mono as Mono } from "next/font/google";
import { cn } from "@/lib/utils";
import { Analytics } from "@vercel/analytics/react";
import { Navbar } from "@/components/nav";
import { Footer } from "@/components/footer";
import { GradientManager } from "@/components/gradient-manager";

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
        <head>
          <link
            href="https://api.fontshare.com/v2/css?f[]=switzer@1,2&display=swap"
            rel="stylesheet"
          />
          <link rel="icon" href="/lyzr.png" />
        </head>
        <body
          className={cn(
            "min-h-screen bg-background font-sans antialiased",
            // GeistSans.className,
            mono.variable
          )}
        >
          <div id="white-gradient" className="white-gradient w-full h-full transition-all duration-300 fixed top-0 left-0 -z-20"></div>
            <Providers>
              <ThemeProvider
                attribute="class"
                defaultTheme="dark"
                enableSystem
                disableTransitionOnChange
              >
              <div className="relative flex min-h-screen flex-col">
                <GradientManager />
                <Navbar />
                <main className="flex-1 pt-16 pb-16 flex flex-col justify-center">
                  {children}
                </main>
                <Footer />
              </div>
              <Toaster />
              <Analytics />
              </ThemeProvider>
            </Providers>
          
        </body>
      </html>
    </>
  );
}
