"use client";

/**
 * ChatInput — Query input with Enter/Shift+Enter rules.
 * Enter sends, Shift+Enter creates newline.
 *
 * Source: DESIGN_SYSTEM §10.1 Chat behavior, BRAND_IDENTITY micro-copy
 */

import { useState, useRef, useCallback } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { SendHorizontal } from "lucide-react";
import { BRAND_COPY } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  className?: string;
}

export function ChatInput({ onSend, isLoading = false, className }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || isLoading) return;
    onSend(trimmed);
    setValue("");
    textareaRef.current?.focus();
  }, [value, isLoading, onSend]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend]
  );

  return (
    <div
      className={cn(
        "flex items-end gap-2 rounded-xl border bg-card p-2",
        className
      )}
    >
      <Textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={BRAND_COPY.INPUT_PLACEHOLDER}
        className="min-h-[44px] max-h-[200px] resize-none border-0 bg-transparent p-2 shadow-none focus-visible:ring-0"
        rows={1}
        disabled={isLoading}
        aria-label="Ask a question"
      />
      <Button
        size="icon"
        onClick={handleSend}
        disabled={!value.trim() || isLoading}
        className="size-9 shrink-0"
        aria-label="Send question"
      >
        <SendHorizontal className="size-4" />
      </Button>
    </div>
  );
}
