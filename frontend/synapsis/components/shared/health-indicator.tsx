"use client";

/**
 * HealthIndicator — System health status dot with tooltip.
 *
 * Source: DESIGN_SYSTEM §5.5, ARCHITECTURE degraded UX
 */

import { CircleCheck, AlertTriangle, CircleX } from "lucide-react";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { HealthState } from "@/types/contracts";
import { HEALTH_CONFIG } from "@/lib/constants";
import { cn } from "@/lib/utils";

const ICON_MAP = {
  CircleCheck,
  AlertTriangle,
  CircleX,
} as const;

const DOT_COLORS: Record<HealthState, string> = {
  healthy: "bg-confidence-high",
  degraded: "bg-confidence-medium",
  unhealthy: "bg-destructive",
};

interface HealthIndicatorProps {
  status: HealthState;
  showLabel?: boolean;
  className?: string;
}

export function HealthIndicator({
  status,
  showLabel = false,
  className,
}: HealthIndicatorProps) {
  const config = HEALTH_CONFIG[status];
  const Icon = ICON_MAP[config.icon as keyof typeof ICON_MAP];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <div
          className={cn(
            "flex items-center gap-2 text-muted-foreground",
            className
          )}
          role="status"
          aria-label={config.label}
        >
          <span
            className={cn(
              "inline-block size-2 rounded-full",
              DOT_COLORS[status]
            )}
          />
          {showLabel && (
            <span className="text-xs">{config.label}</span>
          )}
        </div>
      </TooltipTrigger>
      <TooltipContent>
        <div className="flex items-center gap-1.5">
          <Icon className="size-3.5" />
          <span className="text-xs">{config.label}</span>
        </div>
      </TooltipContent>
    </Tooltip>
  );
}
