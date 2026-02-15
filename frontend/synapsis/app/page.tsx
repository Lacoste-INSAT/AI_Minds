"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { useConfig } from "@/hooks/use-config";

export default function HomePage() {
  const router = useRouter();
  const { data, status } = useConfig();

  useEffect(() => {
    if (status !== "success") {
      if (status === "error") {
        router.replace("/setup");
      }
      return;
    }

    const hasConfiguredDirectories =
      (data?.watched_directories.length ?? 0) > 0;

    router.replace(hasConfiguredDirectories ? "/chat" : "/setup");
  }, [data, router, status]);

  return (
    <div className="flex h-screen items-center justify-center">
      <div
        className="flex items-center gap-2 text-sm text-muted-foreground"
        role="status"
        aria-live="polite"
      >
        <Loader2 className="h-4 w-4 animate-spin" />
        <span>Preparing your workspace...</span>
      </div>
    </div>
  );
}
