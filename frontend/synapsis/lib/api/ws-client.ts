/**
 * WebSocket client for Synapsis streaming endpoints.
 * Handles query streaming and ingestion live events.
 *
 * Source: ARCHITECTURE.md, BACKEND_CONTRACT_ALIGNMENT.md
 */

import { WS_ENDPOINTS } from "./endpoints";
import {
  QueryStreamMessageSchema,
  IngestionWsMessageSchema,
} from "./schemas";
import type {
  QueryStreamMessage,
  QueryStreamRequest,
  IngestionWsMessage,
} from "@/types/contracts";
import { safeJsonParse } from "@/lib/utils";

// ─── Query Stream ───

export interface QueryStreamCallbacks {
  onToken: (token: string) => void;
  onDone: (data: import("@/types/contracts").AnswerPacket) => void;
  onError: (error: string) => void;
  onClose?: () => void;
}

/**
 * Open a streaming query WebSocket.
 * Returns a cleanup function to close the connection.
 */
export function streamQuery(
  request: QueryStreamRequest,
  callbacks: QueryStreamCallbacks
): () => void {
  const ws = new WebSocket(WS_ENDPOINTS.queryStream);
  let closed = false;

  ws.onopen = () => {
    ws.send(JSON.stringify(request));
  };

  ws.onmessage = (event) => {
    const parsed = safeJsonParse<QueryStreamMessage>(event.data);
    if (!parsed) {
      callbacks.onError("Failed to parse stream message");
      return;
    }

    const validated = QueryStreamMessageSchema.safeParse(parsed);
    if (!validated.success) {
      callbacks.onError("Stream message validation failed");
      return;
    }

    const msg = validated.data;
    switch (msg.type) {
      case "token":
        callbacks.onToken(msg.data);
        break;
      case "done":
        callbacks.onDone(msg.data);
        break;
      case "error":
        callbacks.onError(msg.data);
        break;
    }
  };

  ws.onerror = () => {
    if (!closed) callbacks.onError("WebSocket connection error");
  };

  ws.onclose = () => {
    closed = true;
    callbacks.onClose?.();
  };

  return () => {
    closed = true;
    if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
      ws.close();
    }
  };
}

// ─── Ingestion Stream ───

export interface IngestionStreamCallbacks {
  onMessage: (message: IngestionWsMessage) => void;
  onError?: (error: string) => void;
  onClose?: () => void;
}

/**
 * Open the ingestion WebSocket for live status events.
 * Returns a cleanup function to close the connection.
 * Auto-reconnects with exponential backoff.
 */
export function connectIngestionStream(
  callbacks: IngestionStreamCallbacks,
  options?: { maxRetries?: number }
): () => void {
  const maxRetries = options?.maxRetries ?? 5;
  let retries = 0;
  let ws: WebSocket | null = null;
  let stopped = false;

  function connect() {
    if (stopped) return;
    ws = new WebSocket(WS_ENDPOINTS.ingestion);

    ws.onopen = () => {
      retries = 0; // reset on successful connection
    };

    ws.onmessage = (event) => {
      const parsed = safeJsonParse<IngestionWsMessage>(event.data);
      if (!parsed) {
        callbacks.onError?.("Ingestion WebSocket message parse failed");
        return;
      }
      const validated = IngestionWsMessageSchema.safeParse(parsed);
      if (!validated.success) {
        callbacks.onError?.("Ingestion WebSocket message validation failed");
        return;
      }
      callbacks.onMessage(validated.data);
    };

    ws.onerror = () => {
      callbacks.onError?.("Ingestion WebSocket error");
    };

    ws.onclose = () => {
      if (stopped) {
        callbacks.onClose?.();
        return;
      }

      if (retries < maxRetries) {
        const delay = Math.min(1000 * Math.pow(2, retries), 30_000);
        retries++;
        setTimeout(connect, delay);
      } else {
        callbacks.onError?.("Ingestion WebSocket: max retries exceeded");
        callbacks.onClose?.();
      }
    };
  }

  connect();

  return () => {
    stopped = true;
    if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
      ws.close();
    }
  };
}
