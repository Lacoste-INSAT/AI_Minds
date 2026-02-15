"use client";

/**
 * PatternsPanel — Collapsible panel showing graph-related patterns/insights.
 * Displayed alongside the graph view when pattern data is available.
 *
 * Source: FE-056 specification
 */

import { TrendingUp, ChevronDown } from "lucide-react";
import { InsightCard } from "@/components/shared/insight-card";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { InsightItem } from "@/types/contracts";
import { useState } from "react";

interface PatternsPanelProps {
  patterns: InsightItem[];
  className?: string;
}

export function PatternsPanel({ patterns, className }: PatternsPanelProps) {
  const [isOpen, setIsOpen] = useState(true);

  if (patterns.length === 0) return null;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className={cn(className)}>
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="w-full justify-between gap-1.5 text-xs text-muted-foreground"
        >
          <span className="flex items-center gap-1.5">
            <TrendingUp className="h-3.5 w-3.5 text-primary" />
            Patterns ({patterns.length})
          </span>
          <ChevronDown
            className={cn(
              "h-3.5 w-3.5 transition-transform",
              isOpen && "rotate-180"
            )}
          />
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <ScrollArea className="max-h-[300px]">
          <div className="space-y-2 p-2">
            {patterns.map((pattern, idx) => (
              <InsightCard
                key={`${pattern.type}-${idx}`}
                insight={pattern}
              />
            ))}
          </div>
        </ScrollArea>
      </CollapsibleContent>
    </Collapsible>
  );
}
