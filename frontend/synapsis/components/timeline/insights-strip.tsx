"use client";

/**
 * InsightsStrip — Horizontal strip of insight callouts for Timeline view.
 * Shows digest insights non-intrusively above the feed.
 *
 * Source: FE-056 specification
 */

import { Sparkles } from "lucide-react";
import { InsightCard } from "@/components/shared/insight-card";
import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import type { InsightItem } from "@/types/contracts";
import { useState } from "react";

interface InsightsStripProps {
  insights: InsightItem[];
  className?: string;
}

export function InsightsStrip({ insights, className }: InsightsStripProps) {
  const [isOpen, setIsOpen] = useState(true);

  if (insights.length === 0) return null;

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className={cn(className)}>
      <div className="flex items-center justify-between">
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="gap-1.5 text-xs text-muted-foreground"
          >
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            Insights ({insights.length})
          </Button>
        </CollapsibleTrigger>
      </div>
      <CollapsibleContent>
        <ScrollArea className="w-full pb-2">
          <div className="flex gap-3 py-2">
            {insights.map((insight, idx) => (
              <InsightCard
                key={`${insight.type}-${idx}`}
                insight={insight}
                className="min-w-[250px] max-w-[300px] shrink-0"
              />
            ))}
          </div>
          <ScrollBar orientation="horizontal" />
        </ScrollArea>
      </CollapsibleContent>
    </Collapsible>
  );
}
