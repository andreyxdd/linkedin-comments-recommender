"use client";

import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { ResultDisplay } from "@/components/result-display";
import type { SuggestionResult } from "@/lib/types";

const sampleResult: SuggestionResult = {
  partial: true,
  request_summary: "Founder + AI agents + growth loops",
  recovery_message: "Some items were skipped due to rate limits.",
  posts: [
    {
      rank: 1,
      post_url: "https://linkedin.com/posts/example",
      author: "Ada Lovelace",
      author_headline: "Founder at Analytical Engine Labs",
      preview: "Short preview text",
      full_text: "Short preview text\nSecond paragraph starts here.\nTAIL_ONE",
      rationale: "Strong topic match with active engagement.",
      engagement: { reactions: 24, comments: 7 },
      suggested_comments: [
        { id: "c1", text: "Helpful angle one." },
        { id: "c2", text: "Helpful angle two." },
        { id: "c3", text: "Helpful question three?" },
      ],
    },
    {
      rank: 2,
      post_url: "https://linkedin.com/posts/example-2",
      author: "Grace Hopper",
      author_headline: "CTO at Compiler Works",
      preview: "Second preview text",
      full_text: "Second preview text\nMore detail for the next section.\nTAIL_TWO",
      rationale: "Strong operational angle and active engagement.",
      engagement: { reactions: 30, comments: 12 },
      suggested_comments: [
        { id: "c4", text: "Helpful angle four." },
        { id: "c5", text: "Helpful angle five." },
        { id: "c6", text: "Helpful question six?" },
      ],
    },
  ],
};

describe("ResultDisplay", () => {
  it("shows concise result microcopy", () => {
    render(<ResultDisplay result={sampleResult} />);

    expect(screen.getByText("3 ranked posts")).toBeInTheDocument();
    expect(screen.getByText("Partial")).toBeInTheDocument();
    expect(screen.getAllByText("Preview")).toHaveLength(2);
    expect(screen.getAllByText("Why this ranked")).toHaveLength(2);
    expect(screen.getAllByText("Option 1")).toHaveLength(2);
    expect(screen.getAllByText("Option 3")).toHaveLength(2);
    expect(
      screen.getAllByRole("link", { name: "Open on LinkedIn" }),
    ).toHaveLength(2);
  });

  it("uses distinct engagement labels for reactions and comments", () => {
    render(<ResultDisplay result={sampleResult} />);

    expect(screen.getByText("24 reactions")).toHaveClass("bg-sky-100/80");
    expect(screen.getByText("7 comments")).toHaveClass("bg-emerald-100/80");
  });

  it("reveals post continuation inline from the preview boundary", async () => {
    const user = userEvent.setup();
    render(<ResultDisplay result={sampleResult} />);

    expect(screen.queryByText(/TAIL_ONE/)).not.toBeInTheDocument();
    expect(screen.queryByText(/TAIL_TWO/)).not.toBeInTheDocument();

    await user.click(
      screen.getByRole("button", { name: "See more post text for Ada Lovelace" }),
    );

    expect(screen.getByText(/TAIL_ONE/)).toBeInTheDocument();
    expect(screen.queryByText(/TAIL_TWO/)).not.toBeInTheDocument();
  });

  it("copies an option with inline and toast feedback", async () => {
    const user = userEvent.setup();
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, "clipboard", {
      value: { writeText },
      configurable: true,
    });

    render(<ResultDisplay result={sampleResult} />);

    await user.click(
      screen.getByRole("button", { name: "Copy option 1 for Ada Lovelace" }),
    );

    expect(writeText).toHaveBeenCalledWith("Helpful angle one.");
    expect(
      screen.getByRole("button", { name: "Copied option 1 for Ada Lovelace" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "Comment copied to clipboard.",
    );

    await waitFor(
      () => expect(screen.queryByRole("status")).not.toBeInTheDocument(),
      { timeout: 3000 },
    );
  });

  it("renders comment options in a horizontally scrollable row", () => {
    render(<ResultDisplay result={sampleResult} />);

    const firstRow = screen
      .getAllByText("Option 1")[0]
      .closest('[data-testid="comment-options-row"]');
    expect(firstRow).toHaveClass("overflow-x-auto");
  });

  it("preserves newline formatting in preview text", () => {
    render(<ResultDisplay result={sampleResult} />);

    const previewBlock = screen
      .getByRole("button", { name: "See more post text for Ada Lovelace" })
      .closest("p");

    expect(previewBlock).toHaveClass("whitespace-pre-wrap");
  });
});
