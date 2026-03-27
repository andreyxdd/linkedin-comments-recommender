"use client";

import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { GenerationForm } from "@/components/generation-form";

describe("GenerationForm", () => {
  it("submits the structured LinkedIn request once required inputs are present", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<GenerationForm onSubmit={onSubmit} isLoading={false} />);

    const submitButton = screen.getByRole("button", {
      name: /find ranked linkedin opportunities/i,
    });
    expect(submitButton).toBeDisabled();

    await user.selectOptions(screen.getByLabelText(/persona/i), "Founder");
    await user.selectOptions(screen.getByLabelText(/topic/i), "AI agents");
    await user.type(screen.getByLabelText(/include-only keywords/i), "linkedin growth");
    await user.click(screen.getByRole("button", { name: /add keyword/i }));

    expect(screen.getByLabelText(/persona/i)).toHaveValue("Founder");
    expect(screen.getByLabelText(/topic/i)).toHaveValue("AI agents");
    expect(submitButton).toBeEnabled();

    await user.click(submitButton);

    expect(onSubmit).toHaveBeenCalledWith({
      persona: "Founder",
      topic: "AI agents",
      keywords: ["linkedin growth"],
      tone: {
        professional_casual: 50,
        reserved_warm: 50,
        measured_bold: 50,
        conventional_fresh: 50,
      },
    });
  });

  it("uses custom persona and topic overrides when selected", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    render(<GenerationForm onSubmit={onSubmit} isLoading={false} />);

    await user.selectOptions(screen.getByLabelText(/persona/i), "custom");
    await user.type(screen.getByLabelText(/custom persona/i), "Community-led founder");
    await user.selectOptions(screen.getByLabelText(/topic/i), "custom");
    await user.type(screen.getByLabelText(/custom topic/i), "Creator partnerships");
    await user.type(screen.getByLabelText(/include-only keywords/i), "brand affinity");
    await user.click(screen.getByRole("button", { name: /add keyword/i }));

    fireEvent.change(screen.getByLabelText(/reserved <-> warm/i), {
      target: { value: "74" },
    });

    await user.click(
      screen.getByRole("button", { name: /find ranked linkedin opportunities/i }),
    );

    expect(onSubmit).toHaveBeenCalledWith(
      expect.objectContaining({
        persona: "Community-led founder",
        topic: "Creator partnerships",
        keywords: ["brand affinity"],
        tone: expect.objectContaining({
          reserved_warm: 74,
        }),
      }),
    );
  });

  it("preserves entered inputs while loading state toggles", async () => {
    const user = userEvent.setup();
    const onSubmit = vi.fn();

    const { rerender } = render(
      <GenerationForm onSubmit={onSubmit} isLoading={false} />,
    );

    await user.selectOptions(screen.getByLabelText(/persona/i), "Founder");
    await user.selectOptions(screen.getByLabelText(/topic/i), "AI agents");
    await user.type(screen.getByLabelText(/include-only keywords/i), "distribution");
    await user.click(screen.getByRole("button", { name: /add keyword/i }));

    rerender(<GenerationForm onSubmit={onSubmit} isLoading={true} />);
    rerender(<GenerationForm onSubmit={onSubmit} isLoading={false} />);

    expect(screen.getByLabelText(/persona/i)).toHaveValue("Founder");
    expect(screen.getByLabelText(/topic/i)).toHaveValue("AI agents");
    expect(screen.getByText("distribution x")).toBeInTheDocument();
  });
});
