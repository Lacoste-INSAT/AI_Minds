"use client";

import { ThemeProvider as NextThemesProvider } from "next-themes";
import type { ComponentProps } from "react";

/**
 * SSR-safe theme provider using next-themes.
 * Strategy: class-based (adds .dark to <html>)
 * Default: system preference
 * Storage: localStorage key "synapsis-theme"
 *
 * Source: DESIGN_SYSTEM §1.1 "Dark-First, Light-Ready"
 */
export function ThemeProvider({
  children,
  ...props
}: ComponentProps<typeof NextThemesProvider>) {
  return (
    <NextThemesProvider
      attribute="class"
      defaultTheme="dark"
      enableSystem
      disableTransitionOnChange
      storageKey="synapsis-theme"
      {...props}
    >
      {children}
    </NextThemesProvider>
  );
}
