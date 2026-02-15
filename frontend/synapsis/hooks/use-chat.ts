"use client";

/**
 * React hook for chat query operations.
 * Supports both streaming (WS) and request-response (REST) modes.
 * Falls back to REST if streaming fails.
 */

import { useState, useCallback, useRef } from "react";
import type { AnswerPacket, QueryRequest } from "@/types/contracts";
import type { ChatMessage, AsyncStatus } from "@/types/ui";
import { apiClient } from "@/lib/api/client";
import { streamQuery } from "@/lib/api/ws-client";
import { MOCK_ANSWER_HIGH } from "@/mocks/fixtures";
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

    // Try streaming first
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
          // Fallback to REST
          const request: QueryRequest = { question };
          const result = await apiClient.ask(request);

          if (result.ok) {
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: result.data.answer,
                      answer: result.data,
                      isStreaming: false,
                    }
                  : m
              )
            );
            setStatus("success");
          } else {
            // Final fallback to mock
            setMessages((prev) =>
              prev.map((m) =>
                m.id === assistantId
                  ? {
                      ...m,
                      content: MOCK_ANSWER_HIGH.answer,
                      answer: MOCK_ANSWER_HIGH,
                      isStreaming: false,
                    }
                  : m
              )
            );
            setStatus("success");
            setError(wsError);
          }
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
