"use client";

import { useState, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

interface ExclusionRulesProps {
  exclusions: string[];
  onChange: (patterns: string[]) => void;
  className?: string;
}

export function ExclusionRules({
  exclusions,
  onChange,
  className,
}: ExclusionRulesProps) {
  const [value, setValue] = useState("");

  const addPattern = useCallback(() => {
    const nextPattern = value.trim();
    if (!nextPattern || exclusions.includes(nextPattern)) {
      return;
    }
    onChange([...exclusions, nextPattern]);
    setValue("");
  }, [exclusions, onChange, value]);

  const removePattern = useCallback(
    (pattern: string) => {
      onChange(exclusions.filter((item) => item !== pattern));
    },
    [exclusions, onChange]
  );

  return (
    <div className={cn("space-y-4", className)}>
      <p className="text-sm text-muted-foreground">
        Add glob patterns for files or folders to exclude from indexing.
      </p>

      <div className="flex gap-2">
        <Input
          placeholder="e.g. *.log, node_modules/**, .git/**"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              addPattern();
            }
          }}
          className="text-sm font-mono"
          aria-label="Exclusion pattern input"
        />
        <Button
          variant="secondary"
          size="sm"
          onClick={addPattern}
          disabled={!value.trim()}
        >
          Add
        </Button>
      </div>

      {exclusions.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {exclusions.map((pattern) => (
            <Badge key={pattern} variant="secondary" className="gap-1 font-mono text-xs">
              {pattern}
              <button
                type="button"
                onClick={() => removePattern(pattern)}
                className="rounded-sm hover:text-destructive focus:outline-none focus:ring-1 focus:ring-ring"
                aria-label={`Remove ${pattern}`}
              >
                ×
              </button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}

