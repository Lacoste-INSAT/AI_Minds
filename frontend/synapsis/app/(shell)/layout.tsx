import { MainShell } from "@/components/layout/main-shell";
import { CommandPalette } from "@/components/search/command-palette";

/**
 * Shell layout wrapping all app routes with sidebar + header.
 * Applied to /chat, /graph, /timeline, /search, /setup.
 * Includes global Cmd-K command palette.
 */
export default function ShellLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <MainShell>
      {children}
      <CommandPalette />
    </MainShell>
  );
}
