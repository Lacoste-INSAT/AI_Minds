"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  MessageSquare, Network, Clock, Lightbulb, Settings, Brain,
} from "lucide-react";
import {
  Sidebar, SidebarContent, SidebarHeader, SidebarRail,
  SidebarGroup, SidebarGroupLabel, SidebarMenu,
  SidebarMenuButton, SidebarMenuItem,
} from "@/components/ui/sidebar";

const NAV = [
  { href: "/",         label: "Chat",            icon: MessageSquare },
  { href: "/graph",    label: "Knowledge Graph",  icon: Network },
  { href: "/timeline", label: "Timeline",         icon: Clock },
  { href: "/digest",   label: "Insights",         icon: Lightbulb },
  { href: "/setup",    label: "Settings",         icon: Settings },
];

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
  const pathname = usePathname();

  return (
    <Sidebar collapsible="icon" {...props}>
      <SidebarHeader>
        <div className="flex items-center gap-2 px-2 py-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Brain className="h-4 w-4" />
          </div>
          <div className="grid leading-tight group-data-[collapsible=icon]:hidden">
            <span className="font-semibold text-sm">Synapsis</span>
            <span className="text-xs text-muted-foreground">Personal AI</span>
          </div>
        </div>
      </SidebarHeader>

      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Navigation</SidebarGroupLabel>
          <SidebarMenu>
            {NAV.map(({ href, label, icon: Icon }) => (
              <SidebarMenuItem key={href}>
                <SidebarMenuButton
                  asChild
                  className={`h-9 ${pathname === href ? "bg-accent" : ""}`}
                >
                  <Link href={href}>
                    <Icon className="mr-2 h-4 w-4" />
                    <span className="truncate">{label}</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>
            ))}
          </SidebarMenu>
        </SidebarGroup>
      </SidebarContent>

      <SidebarRail />
    </Sidebar>
  );
}
