"use client";

import { render, screen } from "@testing-library/react";

import { StreamDisplay } from "@/components/stream-display";
import type { StreamEvent } from "@/lib/types";

function buildEvent(overrides: Partial<StreamEvent>): StreamEvent {
  return {
    event_type: "status",
    node: "input",
    message: "Locking in your positioning",
    data: {},
    ...overrides,
  };
}

describe("StreamDisplay", () => {
  it("shows the first user-facing milestone when the run starts", () => {
    render(
      <StreamDisplay
        events={[buildEvent({ node: "input" })]}
        isLoading={true}
      />,
    );

    expect(screen.getByText("Find relevant posts")).toBeInTheDocument();
    expect(screen.queryByText("Lock in the request")).not.toBeInTheDocument();
    expect(screen.getByText("Preparing discovery")).toBeInTheDocument();
  });

  it("maps backend ranking updates onto the second visible milestone", () => {
    render(
      <StreamDisplay
        events={[
          buildEvent({ node: "input" }),
          buildEvent({
            node: "discovery",
            message: "Searching public LinkedIn posts",
          }),
          buildEvent({
            node: "ranking",
            message: "Scoring relevance and engagement",
          }),
        ]}
        isLoading={true}
      />,
    );

    expect(screen.getByText("Rank the shortlist")).toBeInTheDocument();
    expect(screen.getByText("Ranking top matches")).toBeInTheDocument();
    expect(screen.getAllByText("Done")).toHaveLength(1);
    expect(screen.getByText("Now")).toBeInTheDocument();
  });

  it("shows the final milestone copy instead of the raw result event message", () => {
    render(
      <StreamDisplay
        events={[
          buildEvent({ node: "input" }),
          buildEvent({
            node: "comment_generation",
            message: "Generating tailored comments",
          }),
          buildEvent({
            event_type: "result",
            node: "complete",
            message: "Suggestions ready.",
          }),
        ]}
        isLoading={false}
      />,
    );

    expect(
      screen.getByText("Suggestions ready to review."),
    ).toBeInTheDocument();
    expect(screen.queryByText("Suggestions ready.")).not.toBeInTheDocument();
    expect(screen.getAllByText("Done")).toHaveLength(3);
    expect(
      screen.getByText("Prepare three ready comments for each top post."),
    ).toBeInTheDocument();
  });
});
