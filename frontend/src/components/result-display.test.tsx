"use client";

import { render, screen } from "@testing-library/react";

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
      rationale: "Strong topic match with active engagement.",
      engagement: { reactions: 24, comments: 7 },
      suggested_comments: [
        { id: "c1", text: "Helpful angle one." },
        { id: "c2", text: "Helpful angle two." },
      ],
    },
  ],
};

describe("ResultDisplay", () => {
  it("shows concise result microcopy", () => {
    render(<ResultDisplay result={sampleResult} />);

    expect(screen.getByText("3 ranked posts")).toBeInTheDocument();
    expect(screen.getByText("Partial")).toBeInTheDocument();
    expect(screen.getByText("Preview")).toBeInTheDocument();
    expect(screen.getByText("Why this ranked")).toBeInTheDocument();
    expect(screen.getByText("Option 1")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Open on LinkedIn" })).toBeInTheDocument();
  });
});
