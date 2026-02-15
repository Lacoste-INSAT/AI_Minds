import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { ThemeProvider } from "@/components/providers/theme-provider";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Toaster } from "@/components/ui/sonner";
import { SkipLink } from "@/components/shared/skip-link";
import "./globals.css";

/**
 * Geist Sans & Mono — self-hosted via next/font/google (fetched at build, not runtime).
 * Source: DESIGN_SYSTEM §3 — Typography
 */
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Synapsis",
  description: "Your knowledge, connected.",
};

/**
 * Root layout with provider stack.
 * - suppressHydrationWarning: required for next-themes class injection
 * - ThemeProvider: dark-first, class strategy, SSR-safe
 * - TooltipProvider: global tooltip context for shadcn tooltips
 * - Toaster: sonner toast notifications
 */
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="color-scheme" content="dark light" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <ThemeProvider>
          <TooltipProvider delayDuration={300}>
            <SkipLink />
            {children}
          </TooltipProvider>
          <Toaster position="bottom-right" richColors closeButton />
        </ThemeProvider>
      </body>
    </html>
  );
}
