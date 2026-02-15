"use client";

/**
 * ConfidenceBadge — Displays confidence level with color-coded icon.
 * 4 states: high, medium, low, none.
 *
 * Source: DESIGN_SYSTEM §2.3, ARCHITECTURE Trust UX
 */

import {
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
  ShieldX,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { ConfidenceLevel } from "@/types/contracts";
import { CONFIDENCE_CONFIG } from "@/lib/constants";
import { cn } from "@/lib/utils";

const ICON_MAP = {
  ShieldCheck,
  ShieldAlert,
  ShieldQuestion,
  ShieldX,
} as const;

interface ConfidenceBadgeProps {
  level: ConfidenceLevel;
  showLabel?: boolean;
  score?: number;
  className?: string;
}

export function ConfidenceBadge({
  level,
  showLabel = true,
  score,
  className,
}: ConfidenceBadgeProps) {
  const config = CONFIDENCE_CONFIG[level];
  const Icon = ICON_MAP[config.icon as keyof typeof ICON_MAP];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge
          variant="outline"
          className={cn(
            "gap-1.5 border-transparent font-mono text-xs",
            className
          )}
          style={{ color: config.colorVar }}
        >
          <Icon className="size-3.5" />
          {showLabel && <span>{config.label}</span>}
          {score !== undefined && (
            <span className="opacity-70">
              {Math.round(score * 100)}%
            </span>
          )}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        <p className="max-w-[220px] text-xs">{config.description}</p>
      </TooltipContent>
    </Tooltip>
  );
}
