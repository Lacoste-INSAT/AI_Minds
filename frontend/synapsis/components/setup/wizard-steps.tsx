"use client";

/**
 * WizardSteps — Multi-step setup wizard for Synapsis.
 * Steps: Welcome → Directories → Exclusions → Complete.
 *
 * Source: ARCHITECTURE.md §Setup, DESIGN_SYSTEM.md, BRAND_IDENTITY.md
 */

import { useCallback } from "react";
import type { ElementType } from "react";
import {
  Brain,
  ChevronRight,
  ChevronLeft,
  Check,
  FolderOpen,
  Filter,
  Sparkles,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { DirectoryPicker } from "./directory-picker";
import { ExclusionRules } from "./exclusion-rules";
import { SETUP_STEPS, BRAND_COPY } from "@/lib/constants";
import { cn } from "@/lib/utils";
import type { SetupStep, SetupState } from "@/types/ui";

// ── Props ──

interface WizardStepsProps {
  state: SetupState;
  onStateChange: (partial: Partial<SetupState>) => void;
  onComplete: () => void;
  isSaving?: boolean;
  className?: string;
}

const STEP_ICONS: Record<SetupStep, ElementType> = {
  welcome: Brain,
  directories: FolderOpen,
  exclusions: Filter,
  complete: Sparkles,
};

const STEP_ORDER: SetupStep[] = ["welcome", "directories", "exclusions", "complete"];

export function WizardSteps({
  state,
  onStateChange,
  onComplete,
  isSaving = false,
  className,
}: WizardStepsProps) {
  const currentIdx = STEP_ORDER.indexOf(state.currentStep);

  const goNext = useCallback(() => {
    if (currentIdx < STEP_ORDER.length - 1) {
      onStateChange({ currentStep: STEP_ORDER[currentIdx + 1] });
    }
  }, [currentIdx, onStateChange]);

  const goBack = useCallback(() => {
    if (currentIdx > 0) {
      onStateChange({ currentStep: STEP_ORDER[currentIdx - 1] });
    }
  }, [currentIdx, onStateChange]);

  const canProceed = (): boolean => {
    switch (state.currentStep) {
      case "welcome":
        return true;
      case "directories":
        return state.directories.length > 0;
      case "exclusions":
        return true;
      case "complete":
        return true;
      default:
        return false;
    }
  };

  return (
    <div className={cn("mx-auto max-w-2xl space-y-6", className)}>
      {/* Step indicator */}
      <nav aria-label="Setup progress" className="flex items-center justify-center gap-2">
        {SETUP_STEPS.map((step, i) => {
          const StepIcon = STEP_ICONS[step.key];
          const isCurrent = step.key === state.currentStep;
          const isCompleted = i < currentIdx;
          return (
            <div key={step.key} className="flex items-center gap-2">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-full border-2 transition-colors",
                  isCurrent && "border-primary bg-primary text-primary-foreground",
                  isCompleted && "border-primary bg-primary/10 text-primary",
                  !isCurrent && !isCompleted && "border-muted text-muted-foreground"
                )}
                aria-current={isCurrent ? "step" : undefined}
                aria-label={`${step.title}${isCompleted ? " (completed)" : ""}`}
              >
                {isCompleted ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <StepIcon className="h-4 w-4" />
                )}
              </div>
              {i < SETUP_STEPS.length - 1 && (
                <div
                  className={cn(
                    "h-0.5 w-8",
                    isCompleted ? "bg-primary" : "bg-muted"
                  )}
                  aria-hidden
                />
              )}
            </div>
          );
        })}
      </nav>

      {/* Step content */}
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-xl">
            {SETUP_STEPS[currentIdx].title}
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            {SETUP_STEPS[currentIdx].description}
          </p>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* WELCOME */}
          {state.currentStep === "welcome" && (
            <div className="space-y-4 text-center">
              <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
                <Brain className="h-8 w-8 text-primary" aria-hidden />
              </div>
              <h2 className="text-lg font-semibold">{BRAND_COPY.FIRST_RUN_TITLE}</h2>
              <p className="text-sm text-muted-foreground">
                {BRAND_COPY.FIRST_RUN_SUBTITLE}
              </p>
              <p className="text-sm text-muted-foreground">
                Select the directories on your machine that contain the documents you
                want Synapsis to learn from. All processing stays local.
              </p>
            </div>
          )}

          {/* DIRECTORIES */}
          {state.currentStep === "directories" && (
            <DirectoryPicker
              directories={state.directories}
              onDirectoriesChange={(dirs) => onStateChange({ directories: dirs })}
            />
          )}

          {/* EXCLUSIONS */}
          {state.currentStep === "exclusions" && (
            <ExclusionRules
              exclusions={state.exclusions}
              onChange={(patterns) => onStateChange({ exclusions: patterns })}
            />
          )}

          {/* COMPLETE */}
          {state.currentStep === "complete" && (
            <div className="space-y-4">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-green-500/10">
                <Check className="h-6 w-6 text-green-500" aria-hidden />
              </div>
              <p className="text-center text-sm text-muted-foreground">
                Review your configuration before saving.
              </p>

              <Separator />

              <div className="space-y-3 text-sm">
                <div>
                  <h4 className="font-semibold">Knowledge Sources</h4>
                  <div className="mt-1 space-y-1">
                    {state.directories.map((dir) => (
                      <div key={dir} className="flex items-center gap-2 text-muted-foreground">
                        <FolderOpen className="h-3.5 w-3.5" aria-hidden />
                        <span className="font-mono text-xs">{dir}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {state.exclusions.length > 0 && (
                  <div>
                    <h4 className="font-semibold">Exclusion Patterns</h4>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {state.exclusions.map((pattern) => (
                        <Badge key={pattern} variant="outline" className="font-mono text-[10px]">
                          {pattern}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Navigation buttons */}
      <div className="flex items-center justify-between">
        <Button
          variant="outline"
          onClick={goBack}
          disabled={currentIdx === 0}
          className="gap-1.5"
        >
          <ChevronLeft className="h-4 w-4" />
          Back
        </Button>

        {state.currentStep === "complete" ? (
          <Button
            onClick={onComplete}
            disabled={isSaving}
            className="gap-1.5"
          >
            {isSaving ? "Saving..." : "Save & Start"}
            {!isSaving && <Check className="h-4 w-4" />}
          </Button>
        ) : (
          <Button
            onClick={goNext}
            disabled={!canProceed()}
            className="gap-1.5"
          >
            Next
            <ChevronRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  );
}
