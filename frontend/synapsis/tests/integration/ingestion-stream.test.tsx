import { describe, it, expect, vi, beforeAll, beforeEach } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { IngestionStreamCallbacks } from "@/lib/api/ws-client";

const mockRefetch = vi.fn();
let capturedCallbacks: IngestionStreamCallbacks | null = null;
let useIngestionStream: typeof import("@/hooks/use-ingestion-stream").useIngestionStream;

vi.mock("@/hooks/use-ingestion-status", () => ({
  useIngestionStatus: () => ({
    status: "success",
    data: null,
    error: null,
    refetch: mockRefetch,
    triggerScan: vi.fn(),
  }),
}));

vi.mock("@/lib/api/ws-client", () => ({
  connectIngestionStream: (callbacks: IngestionStreamCallbacks) => {
    capturedCallbacks = callbacks;
    return () => {
      capturedCallbacks = null;
    };
  },
}));

describe("useIngestionStream", () => {
  beforeAll(async () => {
    ({ useIngestionStream } = await import("@/hooks/use-ingestion-stream"));
  });

  beforeEach(() => {
    capturedCallbacks = null;
    mockRefetch.mockReset();
  });

  it("handles fixture-driven websocket events, including out-of-order updates", async () => {
    const { result } = renderHook(() => useIngestionStream());
    expect(capturedCallbacks).toBeTruthy();

    act(() => {
      capturedCallbacks?.onMessage({ event: "scan_completed", payload: {} });
      capturedCallbacks?.onMessage({
        event: "scan_started",
        payload: { source: "manual" },
      });
    });

    await waitFor(() => {
      expect(result.current.events.length).toBe(2);
    });

    expect(result.current.events[0].type).toBe("scan_started");
    expect(result.current.events[1].type).toBe("scan_completed");
    expect(mockRefetch).toHaveBeenCalled();
  });

  it("falls back to polling when websocket errors", async () => {
    const { result } = renderHook(() => useIngestionStream());
    expect(capturedCallbacks).toBeTruthy();

    act(() => {
      capturedCallbacks?.onError?.("socket error");
    });

    await waitFor(() => {
      expect(result.current.isConnected).toBe(false);
    });
  });
});
