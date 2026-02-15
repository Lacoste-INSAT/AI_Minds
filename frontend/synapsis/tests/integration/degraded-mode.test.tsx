/**
 * Integration Tests — Degraded-Mode UX States
 *
 * Tests that UI components correctly render healthy/degraded/unhealthy states
 * when backend services are partially or fully unavailable.
 *
 * Source: FE-058 specification
 */

import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { TooltipProvider } from "@/components/ui/tooltip";
import { HealthIndicator } from "@/components/shared/health-indicator";
import { ErrorAlert } from "@/components/shared/error-alert";
import { ConfidenceBadge } from "@/components/shared/confidence-badge";
import {
  MOCK_HEALTH_HEALTHY,
  MOCK_HEALTH_DEGRADED,
  MOCK_HEALTH_UNHEALTHY,
  MOCK_ANSWER_ABSTENTION,
} from "@/mocks/fixtures";
import type { HealthResponse } from "@/types/contracts";

// ─── Wrapper for Tooltip Provider ───

function renderWithTooltip(ui: React.ReactElement) {
  return render(<TooltipProvider>{ui}</TooltipProvider>);
}

// ─── HealthIndicator: Healthy / Degraded / Unhealthy states ───

describe("Degraded-Mode: HealthIndicator", () => {
  it("renders healthy state with correct aria label", () => {
    renderWithTooltip(
      <HealthIndicator status="healthy" showLabel />
    );
    const el = screen.getByRole("status");
    expect(el).toHaveAttribute("aria-label");
    expect(el.getAttribute("aria-label")).toMatch(/healthy|all systems/i);
  });

  it("renders degraded state with correct aria label", () => {
    renderWithTooltip(
      <HealthIndicator status="degraded" showLabel />
    );
    const el = screen.getByRole("status");
    expect(el).toHaveAttribute("aria-label");
    expect(el.getAttribute("aria-label")).toMatch(/degraded|partial/i);
  });

  it("renders unhealthy state with correct aria label", () => {
    renderWithTooltip(
      <HealthIndicator status="unhealthy" showLabel />
    );
    const el = screen.getByRole("status");
    expect(el).toHaveAttribute("aria-label");
    expect(el.getAttribute("aria-label")).toMatch(/unhealthy|offline|issues/i);
  });

  it("shows label text when showLabel is true", () => {
    renderWithTooltip(
      <HealthIndicator status="degraded" showLabel />
    );
    // Label text should be visible
    const el = screen.getByRole("status");
    expect(el.textContent).toBeTruthy();
  });

  it("hides label text when showLabel is false", () => {
    renderWithTooltip(
      <HealthIndicator status="healthy" showLabel={false} />
    );
    const el = screen.getByRole("status");
    // Should only have the dot, no text content
    expect(el.querySelector("span.text-xs")).toBeFalsy();
  });
});

// ─── ErrorAlert: Degraded banners ───

describe("Degraded-Mode: ErrorAlert", () => {
  it("renders error severity with role=alert", () => {
    render(
      <ErrorAlert
        message="Backend service is unavailable."
        severity="error"
      />
    );
    expect(screen.getByRole("alert")).toBeTruthy();
    expect(screen.getByText("Backend service is unavailable.")).toBeTruthy();
  });

  it("renders warning severity for degraded state", () => {
    render(
      <ErrorAlert
        title="Partial Service"
        message="Qdrant is offline. Search results may be limited."
        severity="warning"
      />
    );
    expect(screen.getByText("Partial Service")).toBeTruthy();
    expect(
      screen.getByText("Qdrant is offline. Search results may be limited.")
    ).toBeTruthy();
  });

  it("renders info severity for informational messages", () => {
    render(
      <ErrorAlert
        message="Running in offline mode."
        severity="info"
      />
    );
    expect(screen.getByText("Running in offline mode.")).toBeTruthy();
  });

  it("shows retry button when onRetry is provided", () => {
    render(
      <ErrorAlert message="Connection failed." onRetry={() => {}} />
    );
    expect(screen.getByText("Retry")).toBeTruthy();
  });

  it("shows dismiss button when onDismiss is provided", () => {
    render(
      <ErrorAlert message="Warning." onDismiss={() => {}} />
    );
    expect(screen.getByLabelText("Dismiss alert")).toBeTruthy();
  });

  it("hides retry/dismiss when callbacks not provided", () => {
    render(<ErrorAlert message="Just info." />);
    expect(screen.queryByText("Retry")).toBeFalsy();
    expect(screen.queryByLabelText("Dismiss alert")).toBeFalsy();
  });
});

// ─── ConfidenceBadge: Abstention state ───

describe("Degraded-Mode: ConfidenceBadge abstention", () => {
  it("renders none confidence without fabricating certainty", () => {
    renderWithTooltip(<ConfidenceBadge level="none" />);
    // Should render "No confidence" label
    const el = screen.getByText(/no confidence/i);
    expect(el).toBeTruthy();
  });

  it("renders low confidence state", () => {
    renderWithTooltip(<ConfidenceBadge level="low" />);
    const el = screen.getByText(/low confidence/i);
    expect(el).toBeTruthy();
  });
});

// ─── Mock Data Validation: Degraded fixtures completeness ───

describe("Degraded-Mode: Fixture data integrity", () => {
  function assertServiceShape(health: HealthResponse) {
    expect(health.ollama).toBeDefined();
    expect(health.qdrant).toBeDefined();
    expect(health.sqlite).toBeDefined();
    expect(["up", "down"]).toContain(health.ollama.status);
    expect(["up", "down"]).toContain(health.qdrant.status);
    expect(["up", "down"]).toContain(health.sqlite.status);
  }

  it("healthy: all services up", () => {
    expect(MOCK_HEALTH_HEALTHY.status).toBe("healthy");
    assertServiceShape(MOCK_HEALTH_HEALTHY);
    expect(MOCK_HEALTH_HEALTHY.ollama.status).toBe("up");
    expect(MOCK_HEALTH_HEALTHY.qdrant.status).toBe("up");
    expect(MOCK_HEALTH_HEALTHY.sqlite.status).toBe("up");
  });

  it("degraded: at least one service down", () => {
    expect(MOCK_HEALTH_DEGRADED.status).toBe("degraded");
    assertServiceShape(MOCK_HEALTH_DEGRADED);
    const services = [
      MOCK_HEALTH_DEGRADED.ollama.status,
      MOCK_HEALTH_DEGRADED.qdrant.status,
      MOCK_HEALTH_DEGRADED.sqlite.status,
    ];
    expect(services).toContain("down");
  });

  it("unhealthy: multiple services down", () => {
    expect(MOCK_HEALTH_UNHEALTHY.status).toBe("unhealthy");
    assertServiceShape(MOCK_HEALTH_UNHEALTHY);
    const downCount = [
      MOCK_HEALTH_UNHEALTHY.ollama.status,
      MOCK_HEALTH_UNHEALTHY.qdrant.status,
      MOCK_HEALTH_UNHEALTHY.sqlite.status,
    ].filter((s) => s === "down").length;
    expect(downCount).toBeGreaterThanOrEqual(2);
  });

  it("abstention answer has none confidence", () => {
    expect(MOCK_ANSWER_ABSTENTION.confidence).toBe("none");
    expect(MOCK_ANSWER_ABSTENTION.verification).toBe("REJECT");
  });
});
