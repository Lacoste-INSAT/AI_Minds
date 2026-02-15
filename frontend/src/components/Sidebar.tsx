"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Brain, MessageSquare, Clock, GitFork, HardDrive,
  Settings, Shield, Activity, Lightbulb, LayoutDashboard,
} from "lucide-react";

const links = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/query", label: "Ask Synapsis", icon: MessageSquare },
  { href: "/memory", label: "Memory", icon: Clock },
  { href: "/graph", label: "Knowledge Graph", icon: GitFork },
  { href: "/ingestion", label: "Ingestion", icon: HardDrive },
  { href: "/insights", label: "Insights", icon: Lightbulb },
  { href: "/runtime", label: "Runtime", icon: Activity },
  { href: "/security", label: "Security", icon: Shield },
  { href: "/settings", label: "Settings", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 bottom-0 w-60 bg-sidebar-bg border-r border-border flex flex-col z-30">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-border">
        <div className="w-9 h-9 rounded-lg bg-accent/20 flex items-center justify-center">
          <Brain className="w-5 h-5 text-accent-light" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight">Synapsis</h1>
          <p className="text-[10px] text-muted uppercase tracking-widest">Knowledge AI</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 py-3 overflow-y-auto">
        {links.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={`flex items-center gap-3 mx-2 px-3 py-2.5 rounded-lg text-sm transition-all ${
                active
                  ? "bg-accent/15 text-accent-light font-medium"
                  : "text-muted hover:text-foreground hover:bg-card-hover"
              }`}
            >
              <Icon className="w-[18px] h-[18px]" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-border">
        <p className="text-[10px] text-muted">Air-Gapped &bull; Local Only</p>
      </div>
    </aside>
  );
}
