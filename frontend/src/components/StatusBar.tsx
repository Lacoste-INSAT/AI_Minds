"use client";
import { useEffect, useState } from "react";
import { getHealth, type HealthResponse } from "@/lib/api";
import { Wifi, WifiOff } from "lucide-react";

export default function StatusBar() {
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    const poll = () => getHealth().then(setHealth).catch(() => setHealth(null));
    poll();
    const id = setInterval(poll, 15000);
    return () => clearInterval(id);
  }, []);

  const dot = (s?: string) =>
    s === "up"
      ? "bg-success shadow-[0_0_6px_rgba(74,222,128,0.5)]"
      : s === "down"
      ? "bg-danger shadow-[0_0_6px_rgba(248,113,113,0.5)]"
      : "bg-warning shadow-[0_0_6px_rgba(250,204,21,0.4)]";

  return (
    <header className="fixed top-0 left-60 right-0 h-12 bg-sidebar-bg/60 backdrop-blur-xl border-b border-white/[0.06] flex items-center justify-between px-5 z-20">
      <div />
      <div className="flex items-center gap-5 text-xs text-muted">
        {health ? (
          <>
            <span className="flex items-center gap-1.5 hover:text-foreground transition-colors">
              <span className={`w-2 h-2 rounded-full ${dot(health.ollama.status)}`} /> Ollama
            </span>
            <span className="flex items-center gap-1.5 hover:text-foreground transition-colors">
              <span className={`w-2 h-2 rounded-full ${dot(health.qdrant.status)}`} /> Qdrant
            </span>
            <span className="flex items-center gap-1.5 hover:text-foreground transition-colors">
              <span className={`w-2 h-2 rounded-full ${dot(health.sqlite.status)}`} /> SQLite
            </span>
            <span className="h-3 w-px bg-white/[0.08]" />
            <span className="flex items-center gap-1.5 text-success">
              <Wifi className="w-3 h-3" /> Connected
            </span>
          </>
        ) : (
          <span className="flex items-center gap-1.5 text-danger">
            <WifiOff className="w-3 h-3" /> Offline
          </span>
        )}
      </div>
    </header>
  );
}
