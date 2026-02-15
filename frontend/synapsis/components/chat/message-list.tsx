"use client";

/**
 * MessageList — Chat message thread with auto-scroll.
 *
 * Source: DESIGN_SYSTEM §10.1
 */

import { useRef, useEffect } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AnswerCard } from "./answer-card";
import { User, Brain } from "lucide-react";
import type { ChatMessage } from "@/types/ui";
import { BRAND_COPY } from "@/lib/constants";
import { cn } from "@/lib/utils";

interface MessageListProps {
  messages: ChatMessage[];
  onSourceClick?: (messageId: string, sourceIndex: number) => void;
  className?: string;
}

export function MessageList({
  messages,
  onSourceClick,
  className,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className={cn("flex h-full flex-col items-center justify-center gap-4 text-center", className)}>
        <div className="flex size-16 items-center justify-center rounded-2xl bg-primary/10">
          <Brain className="size-8 text-primary" />
        </div>
        <div className="space-y-1">
          <h2 className="text-lg font-semibold">{BRAND_COPY.FIRST_RUN_TITLE}</h2>
          <p className="max-w-md text-sm text-muted-foreground">
            {BRAND_COPY.FIRST_RUN_SUBTITLE}
          </p>
        </div>
        <p className="text-xs text-muted-foreground">
          {BRAND_COPY.INPUT_PLACEHOLDER}
        </p>
      </div>
    );
  }

  return (
    <ScrollArea className={cn("h-full", className)}>
      <div
        className="space-y-6 p-4"
        role="log"
        aria-label="Chat messages"
        aria-live="polite"
        aria-relevant="additions"
      >
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={cn(
              "flex gap-3",
              msg.role === "user" ? "justify-end" : "justify-start"
            )}
            role="article"
            aria-label={msg.role === "user" ? "Your message" : "Synapsis response"}
          >
            {msg.role === "assistant" && (
              <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary/10">
                <Brain className="size-4 text-primary" />
              </div>
            )}
            <div
              className={cn(
                "max-w-[80%] space-y-1",
                msg.role === "user" && "text-right"
              )}
            >
              {msg.role === "user" ? (
                <div className="inline-block rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-primary-foreground">
                  {msg.content}
                </div>
              ) : (
                <AnswerCard
                  content={msg.content}
                  answer={msg.answer}
                  isStreaming={msg.isStreaming}
                  onSourceClick={(index) => onSourceClick?.(msg.id, index)}
                />
              )}
            </div>
            {msg.role === "user" && (
              <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-muted">
                <User className="size-4 text-muted-foreground" />
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </ScrollArea>
  );
}
