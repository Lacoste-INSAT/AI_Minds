"use client";

/**
 * ErrorAlert — Consistent error/warning/info alert component.
 * Used for inline error states, degraded-mode banners, and status messages.
 *
 * Source: DESIGN_SYSTEM §6.4, ARCHITECTURE error-handling patterns
 */

import { AlertCircle, AlertTriangle, Info, X } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

type ErrorSeverity = "error" | "warning" | "info";

interface ErrorAlertProps {
  title?: string;
  message: string;
  severity?: ErrorSeverity;
  onDismiss?: () => void;
  onRetry?: () => void;
  className?: string;
}

const SEVERITY_CONFIG: Record<
  ErrorSeverity,
  {
    icon: React.ComponentType<{ className?: string }>;
    variant: "default" | "destructive";
    defaultTitle: string;
  }
> = {
  error: {
    icon: AlertCircle,
    variant: "destructive",
    defaultTitle: "Something went wrong",
  },
  warning: {
    icon: AlertTriangle,
    variant: "default",
    defaultTitle: "Attention required",
  },
  info: {
    icon: Info,
    variant: "default",
    defaultTitle: "Information",
  },
};

export function ErrorAlert({
  title,
  message,
  severity = "error",
  onDismiss,
  onRetry,
  className,
}: ErrorAlertProps) {
  const config = SEVERITY_CONFIG[severity];
  const Icon = config.icon;

  return (
    <Alert
      variant={config.variant}
      className={cn("relative", className)}
      role="alert"
    >
      <Icon className="h-4 w-4" />
      <AlertTitle>{title ?? config.defaultTitle}</AlertTitle>
      <AlertDescription className="flex items-center justify-between gap-2">
        <span>{message}</span>
        <div className="flex shrink-0 gap-1">
          {onRetry && (
            <Button
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="h-7 text-xs"
            >
              Retry
            </Button>
          )}
          {onDismiss && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
              className="h-7 w-7 p-0"
              aria-label="Dismiss alert"
            >
              <X className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
}
