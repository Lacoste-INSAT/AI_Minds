/**
 * Deterministic WebSocket mock flows for query and ingestion streams.
 */

import type {
  IngestionWsMessage,
  QueryStreamRequest,
} from "@/types/contracts";
import { mockHandlers } from "./handlers";

interface QueryCallbacks {
  onToken: (token: string) => void;
  onDone: (answer: import("@/types/contracts").AnswerPacket) => void;
  onError: (error: string) => void;
  onClose?: () => void;
}

interface IngestionCallbacks {
  onMessage: (message: IngestionWsMessage) => void;
  onError?: (error: string) => void;
  onClose?: () => void;
}

export function streamMockQuery(
  request: QueryStreamRequest,
  callbacks: QueryCallbacks
): () => void {
  let stopped = false;
  let tokenTimer: ReturnType<typeof setInterval> | null = null;

  void (async () => {
    try {
      const answer = await mockHandlers.ask({ question: request.question });
      const tokens = answer.answer.split(" ");
      let index = 0;

      tokenTimer = setInterval(() => {
        if (stopped) {
          if (tokenTimer) {
            clearInterval(tokenTimer);
          }
          return;
        }

        if (index >= tokens.length) {
          if (tokenTimer) {
            clearInterval(tokenTimer);
          }
          callbacks.onDone(answer);
          callbacks.onClose?.();
          return;
        }

        const token = `${tokens[index]}${index < tokens.length - 1 ? " " : ""}`;
        callbacks.onToken(token);
        index += 1;
      }, 35);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Mock stream failure";
      callbacks.onError(message);
      callbacks.onClose?.();
    }
  })();

  return () => {
    stopped = true;
    if (tokenTimer) {
      clearInterval(tokenTimer);
    }
    callbacks.onClose?.();
  };
}

export function connectMockIngestionStream(callbacks: IngestionCallbacks): () => void {
  let stopped = false;
  const events: IngestionWsMessage[] = [
    { event: "status", payload: { queue_depth: 3 } },
    { event: "scan_started", payload: {} },
    { event: "file_processed", payload: { file_name: "architecture-overview.md" } },
    { event: "file_processed", payload: { file_name: "frontend-plan.md" } },
    { event: "scan_completed", payload: {} },
  ];
  let cursor = 0;

  const timer = setInterval(() => {
    if (stopped) {
      clearInterval(timer);
      return;
    }
    callbacks.onMessage(events[cursor]);
    cursor = (cursor + 1) % events.length;
  }, 1500);

  return () => {
    stopped = true;
    clearInterval(timer);
    callbacks.onClose?.();
  };
}

