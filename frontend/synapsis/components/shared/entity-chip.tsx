"use client";

/**
 * EntityChip — Typed entity tag with color and icon.
 *
 * Source: DESIGN_SYSTEM §2.4, Graph node colors
 */

import {
  User,
  Building2,
  FolderKanban,
  Lightbulb,
  MapPin,
  Calendar,
  FileText,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import type { EntityType } from "@/types/ui";
import { ENTITY_TYPE_CONFIG } from "@/lib/constants";
import { cn } from "@/lib/utils";

const ICON_MAP: Record<string, React.ComponentType<{ className?: string; style?: React.CSSProperties }>> = {
  User,
  Building2,
  FolderKanban,
  Lightbulb,
  MapPin,
  Calendar,
  FileText,
};

interface EntityChipProps {
  name: string;
  type: EntityType;
  onClick?: () => void;
  className?: string;
  /** Visual size variant */
  size?: "sm" | "default";
}

export function EntityChip({ name, type, onClick, className, size = "default" }: EntityChipProps) {
  const config = ENTITY_TYPE_CONFIG[type];
  const Icon = ICON_MAP[config.icon];

  const chip = (
    <Badge
      variant="outline"
      className={cn(
        "cursor-default gap-1.5 transition-colors",
        size === "sm" ? "text-[10px] px-1.5 py-0" : "text-xs",
        onClick && "cursor-pointer hover:bg-accent",
        className
      )}
      style={{ borderColor: config.colorVar, color: config.colorVar }}
      onClick={onClick}
      role={onClick ? "button" : undefined}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
    >
      {Icon && <Icon className={size === "sm" ? "size-2.5" : "size-3"} />}
      <span>{name}</span>
    </Badge>
  );

  if (!onClick) return chip;

  return (
    <HoverCard>
      <HoverCardTrigger asChild>{chip}</HoverCardTrigger>
      <HoverCardContent className="w-auto">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="size-4" style={{ color: config.colorVar }} />}
          <div>
            <p className="text-sm font-medium">{name}</p>
            <p className="text-xs text-muted-foreground">{config.label}</p>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}
