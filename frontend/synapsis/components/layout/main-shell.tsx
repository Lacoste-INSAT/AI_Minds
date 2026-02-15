"use client";

/**
 * MainShell — App shell wrapping sidebar + header + content area.
 * Uses shadcn SidebarProvider for collapsible state management.
 * Includes ErrorBoundary for graceful crash recovery.
 *
 * Source: DESIGN_SYSTEM §4.2 Layout Architecture
 */

import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar } from "./app-sidebar";
import { AppHeader } from "./app-header";
import { ErrorBoundary } from "@/components/shared/error-boundary";
import { SystemHealthBanner } from "@/components/shared/system-health-banner";
import { RuntimeIncidentsBanner } from "@/components/shared/runtime-incidents-banner";

interface MainShellProps {
  children: React.ReactNode;
}

export function MainShell({ children }: MainShellProps) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <AppHeader />
        <SystemHealthBanner />
        <RuntimeIncidentsBanner />
        <main id="main-content" className="flex-1 overflow-auto p-6" tabIndex={-1}>
          <ErrorBoundary section="Application">
            {children}
          </ErrorBoundary>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
