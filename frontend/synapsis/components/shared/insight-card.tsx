"use client";

/**
 * InsightCard — Single insight callout with type icon and entity tags.
 * Non-blocking, optional display. Brand-aligned tone.
 *
 * Source: FE-056 specification, DESIGN_SYSTEM §7, BRAND_IDENTITY
 */

import { Lightbulb, TrendingUp, Link2, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { InsightItem } from "@/types/contracts";

interface InsightCardProps {
  insight: InsightItem;
  className?: string;
}

const INSIGHT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  connection: Link2,
  pattern: TrendingUp,
  suggestion: Lightbulb,
};

export function InsightCard({ insight, className }: InsightCardProps) {
  const Icon = INSIGHT_ICONS[insight.type] ?? Info;

  return (
    <Card
      className={cn(
        "border-primary/20 bg-primary/[0.03] transition-colors hover:border-primary/40",
        className
      )}
    >
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium">
          <Icon className="h-4 w-4 text-primary" />
          {insight.title ?? `${insight.type.charAt(0).toUpperCase()}${insight.type.slice(1)}`}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <p className="text-xs text-muted-foreground leading-relaxed">
          {insight.description}
        </p>
        {(insight.related_entities ?? insight.entities)?.length ? (
          <div className="flex flex-wrap gap-1">
            {(insight.related_entities ?? insight.entities)!.map((entity) => (
              <Badge
                key={entity}
                variant="secondary"
                className="text-[10px]"
              >
                {entity}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
