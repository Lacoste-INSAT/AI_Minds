"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { Loader2 } from "lucide-react";
import { API_MODE } from "@/lib/env";
import { useConfig } from "@/hooks/use-config";

const MOCK_SETUP_COMPLETE_KEY = "synapsis.setup.complete";

export default function HomePage() {
  const router = useRouter();
  const { data, status } = useConfig();

  useEffect(() => {
    if (API_MODE === "mock") {
      const isSetupComplete =
        typeof window !== "undefined" &&
        window.localStorage.getItem(MOCK_SETUP_COMPLETE_KEY) === "true";
      router.replace(isSetupComplete ? "/chat" : "/setup");
      return;
    }

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
