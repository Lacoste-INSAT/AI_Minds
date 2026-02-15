import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { SystemHealthBanner } from "@/components/shared/system-health-banner";
import type { HealthResponse } from "@/types/contracts";

const mockUseHealth = vi.fn();

vi.mock("@/hooks/use-health", () => ({
  useHealth: () => mockUseHealth(),
}));

function buildHealth(overrides: Partial<HealthResponse>): HealthResponse {
  return {
    status: "healthy",
    ollama: { status: "up", detail: {} },
    qdrant: { status: "up", detail: {} },
    sqlite: { status: "up", detail: {} },
    disk_free_gb: 100,
    uptime_seconds: 1000,
    ...overrides,
  };
}

describe("SystemHealthBanner", () => {
  it("renders nothing when healthy and no fallback error", () => {
    mockUseHealth.mockReturnValue({
      data: buildHealth({ status: "healthy" }),
      error: null,
      refetch: vi.fn(),
    });

    const { container } = render(<SystemHealthBanner />);
    expect(container.textContent).toBe("");
  });

  it("shows explicit ollama-down degraded banner", () => {
    mockUseHealth.mockReturnValue({
      data: buildHealth({
        status: "degraded",
        ollama: { status: "down", detail: { error: "offline" } },
      }),
      error: null,
      refetch: vi.fn(),
    });

    render(<SystemHealthBanner />);
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByText("System degraded")).toBeTruthy();
    expect(screen.getByText(/Affected services: Ollama/i)).toBeTruthy();
  });

  it("shows explicit qdrant-down degraded banner", () => {
    mockUseHealth.mockReturnValue({
      data: buildHealth({
        status: "degraded",
        qdrant: { status: "down", detail: { error: "offline" } },
      }),
      error: null,
      refetch: vi.fn(),
    });

    render(<SystemHealthBanner />);
    expect(screen.getByText(/Affected services: Qdrant/i)).toBeTruthy();
  });

  it("shows unhealthy banner when sqlite is down with others", () => {
    mockUseHealth.mockReturnValue({
      data: buildHealth({
        status: "unhealthy",
        qdrant: { status: "down", detail: { error: "offline" } },
        sqlite: { status: "down", detail: { error: "io" } },
      }),
      error: null,
      refetch: vi.fn(),
    });

    render(<SystemHealthBanner />);
    expect(screen.getByText("System unhealthy")).toBeTruthy();
    expect(screen.getByText(/Affected services: Qdrant, SQLite/i)).toBeTruthy();
  });
});
