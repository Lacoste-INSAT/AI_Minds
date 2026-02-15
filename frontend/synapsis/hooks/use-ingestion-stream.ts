"use client";

/**
 * useIngestionStream — WebSocket-based ingestion event stream.
 * Consumes WS /ingestion/ws events and merges with polling truth.
 * Falls back to polling when WS disconnects.
 *
 * Source: FE-055 specification, BACKEND_CONTRACT_ALIGNMENT.md
 */

import { useState, useEffect, useCallback, useRef } from "react";
import { toast } from "sonner";
import type { IngestionWsMessage, IngestionWsEventType } from "@/types/contracts";
import type { IngestionUiEvent } from "@/types/ui";
import { connectIngestionStream } from "@/lib/api/ws-client";
import { useIngestionStatus } from "./use-ingestion-status";

interface UseIngestionStreamReturn {
  /** Merged polling + WS status */
  status: ReturnType<typeof useIngestionStatus>;
  /** Recent WS events (last 50) */
  events: IngestionUiEvent[];
  /** Whether WS is currently connected */
  isConnected: boolean;
  /** Clear event log */
  clearEvents: () => void;
}

const MAX_EVENTS = 50;

export function useIngestionStream(): UseIngestionStreamReturn {
  const pollingStatus = useIngestionStatus();
  const [events, setEvents] = useState<IngestionUiEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const cleanupRef = useRef<(() => void) | null>(null);

  const buildEventSummary = (type: IngestionWsEventType): string => {
    switch (type) {
      case "scan_started":
        return "Scan started";
      case "scan_completed":
        return "Scan completed";
      case "file_processed":
        return "File processed";
      case "file_deleted":
        return "File deleted";
      case "file_error":
        return "File processing error";
      case "incident":
        return "Runtime incident";
      default:
        return "Status update";
    }
  };

  const addEvent = useCallback((msg: IngestionWsMessage) => {
    const fileName = typeof msg.payload?.file_name === "string" ? msg.payload.file_name : undefined;
    const event: IngestionUiEvent = {
      type: msg.event,
      raw: msg,
      timestamp: Date.now(),
      fileName,
      summary: buildEventSummary(msg.event),
    };

    setEvents((prev) => [event, ...prev].slice(0, MAX_EVENTS));

    // Toast for important transitions
    switch (msg.event) {
      case "file_error":
        toast.error("Ingestion error", {
          description: `File processing failed: ${(msg.payload?.file_name as string) ?? "unknown"}`,
        });
        break;
      case "scan_completed":
        toast.success("Scan complete", {
          description: "File system scan finished successfully.",
        });
        // Refresh polling data after scan completes
        pollingStatus.refetch();
        break;
      case "scan_started":
        toast.info("Scan started", {
          description: "Scanning watched directories for changes...",
        });
        break;
      case "file_processed":
        // Silent — too noisy to toast every processed file
        // But refresh polling after a batch
        pollingStatus.refetch();
        break;
      case "incident":
        toast.warning("Runtime incident", {
          description: typeof msg.payload?.reason === "string" ? msg.payload.reason : "An incident was reported by backend runtime.",
        });
        break;
    }
  }, [pollingStatus]);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  useEffect(() => {
    cleanupRef.current = connectIngestionStream(
      {
        onMessage: (msg) => {
          setIsConnected(true);
          addEvent(msg);
        },
        onError: () => {
          setIsConnected(false);
        },
        onClose: () => {
          setIsConnected(false);
        },
      },
      { maxRetries: 5 }
    );

    return () => {
      cleanupRef.current?.();
    };
  }, [addEvent]);

  return {
    status: pollingStatus,
    events,
    isConnected,
    clearEvents,
  };
}
