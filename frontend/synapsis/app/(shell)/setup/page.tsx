"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { WizardSteps } from "@/components/setup/wizard-steps";
import { useConfig } from "@/hooks/use-config";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { SetupState } from "@/types/ui";

const MOCK_SETUP_COMPLETE_KEY = "synapsis.setup.complete";

const DEFAULT_EXCLUSIONS = [
  "node_modules/**",
  ".git/**",
  "*.log",
  "__pycache__/**",
];

export default function SetupPage() {
  const router = useRouter();
  const { data, saveConfig, isSaving } = useConfig();
  const initializedFromConfigRef = useRef(false);

  const [state, setState] = useState<SetupState>({
    currentStep: "welcome",
    directories: [],
    exclusions: [...DEFAULT_EXCLUSIONS],
    isComplete: false,
  });

  const updateState = useCallback(
    (partial: Partial<SetupState>) =>
      setState((prev) => ({ ...prev, ...partial })),
    []
  );

  useEffect(() => {
    if (!data || initializedFromConfigRef.current) {
      return;
    }
    const bootstrapTimer = window.setTimeout(() => {
      initializedFromConfigRef.current = true;
      setState((prev) => ({
        ...prev,
        directories: data.watched_directories.map((directory) => directory.path),
        exclusions: data.exclude_patterns.length > 0 ? data.exclude_patterns : prev.exclusions,
      }));
    }, 0);
    return () => {
      window.clearTimeout(bootstrapTimer);
    };
  }, [data]);

  const handleComplete = useCallback(async () => {
    const success = await saveConfig({
      watched_directories: state.directories,
      exclude_patterns: state.exclusions,
    });
    if (success) {
      if (typeof window !== "undefined") {
        window.localStorage.setItem(MOCK_SETUP_COMPLETE_KEY, "true");
      }
      updateState({ isComplete: true });
      router.push("/chat");
    }
  }, [state.directories, state.exclusions, saveConfig, updateState, router]);

  return (
    <ScrollArea className="h-full">
      <div className="py-8">
        <WizardSteps
          state={state}
          onStateChange={updateState}
          onComplete={handleComplete}
          isSaving={isSaving}
        />
      </div>
    </ScrollArea>
  );
}
