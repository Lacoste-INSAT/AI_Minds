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
    <aside className="fixed left-0 top-0 bottom-0 w-60 bg-sidebar-bg/80 backdrop-blur-xl border-r border-white/[0.06] flex flex-col z-30">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-5 border-b border-white/[0.06]">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent/30 to-purple-500/20 flex items-center justify-center ring-1 ring-accent/20 shadow-lg shadow-accent/10">
          <Brain className="w-5 h-5 text-accent-light animate-breathe" />
        </div>
        <div>
          <h1 className="text-base font-bold tracking-tight bg-gradient-to-r from-white to-white/70 bg-clip-text text-transparent">Synapsis</h1>
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
              className={`group flex items-center gap-3 mx-2 px-3 py-2.5 rounded-xl text-sm transition-all ${
                active
                  ? "bg-gradient-to-r from-accent/15 to-purple-500/10 text-accent-light font-medium ring-1 ring-accent/10 shadow-sm shadow-accent/5"
                  : "text-muted hover:text-foreground hover:bg-white/[0.03]"
              }`}
            >
              <Icon className={`w-[18px] h-[18px] transition-transform group-hover:scale-110 ${active ? "drop-shadow-[0_0_4px_rgba(99,102,241,0.4)]" : ""}`} />
              {label}
              {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-accent shadow-[0_0_6px_rgba(99,102,241,0.5)]" />}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-4 border-t border-white/[0.06]">
        <div className="flex items-center gap-2">
          <div className="w-1.5 h-1.5 rounded-full bg-green-400 shadow-[0_0_6px_rgba(74,222,128,0.4)]" />
          <p className="text-[10px] text-muted">Air-Gapped &bull; Local Only</p>
        </div>
      </div>
    </aside>
  );
}
