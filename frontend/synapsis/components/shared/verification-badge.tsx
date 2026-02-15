"use client";

/**
 * VerificationBadge — Displays verification status (APPROVE/REVISE/REJECT).
 *
 * Source: DESIGN_SYSTEM §6.1, ARCHITECTURE Trust UX
 */

import { CheckCircle, AlertCircle, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import type { VerificationStatus } from "@/types/contracts";
import { VERIFICATION_CONFIG } from "@/lib/constants";
import { cn } from "@/lib/utils";

const ICON_MAP = {
  CheckCircle,
  AlertCircle,
  XCircle,
} as const;

interface VerificationBadgeProps {
  status: VerificationStatus;
  showLabel?: boolean;
  className?: string;
}

export function VerificationBadge({
  status,
  showLabel = true,
  className,
}: VerificationBadgeProps) {
  const config = VERIFICATION_CONFIG[status];
  const Icon = ICON_MAP[config.icon as keyof typeof ICON_MAP];

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge
          variant={config.variant}
          className={cn("gap-1.5 text-xs", className)}
        >
          <Icon className="size-3.5" />
          {showLabel && <span>{config.label}</span>}
        </Badge>
      </TooltipTrigger>
      <TooltipContent>
        <p className="max-w-[220px] text-xs">{config.description}</p>
      </TooltipContent>
    </Tooltip>
  );
}
