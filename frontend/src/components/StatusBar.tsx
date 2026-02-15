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
    s === "up" ? "bg-success" : s === "down" ? "bg-danger" : "bg-warning";

  return (
    <header className="fixed top-0 left-60 right-0 h-12 bg-sidebar-bg/80 backdrop-blur border-b border-border flex items-center justify-between px-5 z-20">
      <div />
      <div className="flex items-center gap-4 text-xs text-muted">
        {health ? (
          <>
            <span className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${dot(health.ollama.status)}`} /> Ollama
            </span>
            <span className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${dot(health.qdrant.status)}`} /> Qdrant
            </span>
            <span className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${dot(health.sqlite.status)}`} /> SQLite
            </span>
            <span className="flex items-center gap-1.5">
              <Wifi className="w-3 h-3 text-success" /> Connected
            </span>
          </>
        ) : (
          <span className="flex items-center gap-1.5">
            <WifiOff className="w-3 h-3 text-danger" /> Offline
          </span>
        )}
      </div>
    </header>
  );
}
