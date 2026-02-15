import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import { axe } from "vitest-axe";
import { TooltipProvider } from "@/components/ui/tooltip";
import { HealthIndicator } from "@/components/shared/health-indicator";
import { ErrorAlert } from "@/components/shared/error-alert";
import { ChatInput } from "@/components/chat/chat-input";
import { DirectoryPicker } from "@/components/setup/directory-picker";

describe("A11Y: core UI", () => {
  it("HealthIndicator has no basic accessibility violations", async () => {
    const { container } = render(
      <TooltipProvider>
        <HealthIndicator status="degraded" showLabel />
      </TooltipProvider>
    );
    expect((await axe(container)).violations).toHaveLength(0);
  });

  it("ErrorAlert has no basic accessibility violations", async () => {
    const { container } = render(
      <ErrorAlert
        severity="warning"
        title="Service degraded"
        message="Ollama is unavailable."
        onRetry={() => {}}
      />
    );
    expect((await axe(container)).violations).toHaveLength(0);
  });

  it("ChatInput has no basic accessibility violations", async () => {
    const { container } = render(<ChatInput onSend={() => {}} isLoading={false} />);
    expect((await axe(container)).violations).toHaveLength(0);
  });

  it("DirectoryPicker has no basic accessibility violations", async () => {
    const { container } = render(
      <TooltipProvider>
        <DirectoryPicker directories={["C:\\Knowledge"]} onDirectoriesChange={() => {}} />
      </TooltipProvider>
    );
    expect((await axe(container)).violations).toHaveLength(0);
  });
});
