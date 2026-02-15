"use client";

/**
 * React hook for chat query operations.
 * Uses streaming mode (WS) without silent fallback paths.
 */

import { useState, useCallback, useRef } from "react";
import type { AnswerPacket } from "@/types/contracts";
import type { ChatMessage, AsyncStatus } from "@/types/ui";
import { streamQuery } from "@/lib/api/ws-client";
import { createId } from "@/lib/utils";

interface UseChatReturn {
  messages: ChatMessage[];
  status: AsyncStatus;
  error: string | null;
  sendMessage: (question: string) => void;
  clearMessages: () => void;
}

export function useChat(): UseChatReturn {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<AsyncStatus>("idle");
  const [error, setError] = useState<string | null>(null);
  const cleanupRef = useRef<(() => void) | null>(null);

  const sendMessage = useCallback((question: string) => {
    const userMsg: ChatMessage = {
      id: createId(),
      role: "user",
      content: question,
      timestamp: new Date().toISOString(),
    };

    const assistantId = createId();
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
      isStreaming: true,
    };

    setMessages((prev) => [...prev, userMsg, assistantMsg]);
    setStatus("loading");
    setError(null);

    const cleanup = streamQuery(
      { question },
      {
        onToken: (token) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: m.content + token }
                : m
            )
          );
        },
        onDone: (answer: AnswerPacket) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? { ...m, content: answer.answer, answer, isStreaming: false }
                : m
            )
          );
          setStatus("success");
        },
        onError: async (wsError) => {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content: "Unable to complete streaming response.",
                    isStreaming: false,
                  }
                : m
            )
          );
          setStatus("error");
          setError(wsError);
        },
      }
    );

    cleanupRef.current = cleanup;
  }, []);

  const clearMessages = useCallback(() => {
    cleanupRef.current?.();
    setMessages([]);
    setStatus("idle");
    setError(null);
  }, []);

  return { messages, status, error, sendMessage, clearMessages };
}
