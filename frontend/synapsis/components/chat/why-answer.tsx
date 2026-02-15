"use client";

import { useState } from "react";
import { Brain, ChevronDown } from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface WhyAnswerProps {
  reasoning: string;
  defaultOpen?: boolean;
  className?: string;
}

export function WhyAnswer({
  reasoning,
  defaultOpen = false,
  className,
}: WhyAnswerProps) {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  if (!reasoning) {
    return null;
  }

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen} className={className}>
      <CollapsibleTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          className="h-7 gap-1.5 px-2 text-xs text-muted-foreground"
        >
          <Brain className="size-3" />
          Why this answer
          <ChevronDown className={cn("size-3 transition-transform", isOpen && "rotate-180")} />
        </Button>
      </CollapsibleTrigger>
      <CollapsibleContent>
        <div className="mt-2 rounded-lg border bg-muted/50 p-3">
          <p className="whitespace-pre-wrap font-mono text-xs leading-relaxed text-muted-foreground">
            {reasoning}
          </p>
        </div>
      </CollapsibleContent>
    </Collapsible>
  );
}

