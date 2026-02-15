import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { RuntimeIncidentsBanner } from "@/components/shared/runtime-incidents-banner";

const mockUseRuntimeIncidents = vi.fn();

vi.mock("@/hooks/use-runtime-incidents", () => ({
  useRuntimeIncidents: () => mockUseRuntimeIncidents(),
}));

describe("RuntimeIncidentsBanner", () => {
  it("renders incident message when incident exists", () => {
    mockUseRuntimeIncidents.mockReturnValue({
      incidents: [
        {
          id: "incident-001",
          timestamp: "2025-01-01T00:00:00.000Z",
          subsystem: "model_router",
          operation: "query_stream",
          reason: "GPU lane unavailable",
          severity: "error",
          blocked: true,
          payload: { lane: "gpu" },
        },
      ],
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<RuntimeIncidentsBanner />);
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByText(/Runtime incident/i)).toBeTruthy();
    expect(screen.getByText(/GPU lane unavailable/i)).toBeTruthy();
  });

  it("dismisses current incident", () => {
    mockUseRuntimeIncidents.mockReturnValue({
      incidents: [
        {
          id: "incident-001",
          timestamp: "2025-01-01T00:00:00.000Z",
          subsystem: "model_router",
          operation: "query_stream",
          reason: "GPU lane unavailable",
          severity: "error",
          blocked: true,
          payload: { lane: "gpu" },
        },
      ],
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    const { container } = render(<RuntimeIncidentsBanner />);
    fireEvent.click(screen.getByLabelText("Dismiss alert"));
    expect(container.textContent).toBe("");
  });
});

