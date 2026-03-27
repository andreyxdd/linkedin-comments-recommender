"use client";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { StreamEvent } from "@/lib/types";

interface StreamDisplayProps {
  events: StreamEvent[];
  isLoading: boolean;
}

const steps = [
  {
    node: "input",
    title: "Lock in the request",
    detail: "Normalize persona, topic, keywords, and tone.",
  },
  {
    node: "discovery",
    title: "Search public posts",
    detail: "Gather the candidate conversations worth a closer look.",
  },
  {
    node: "ranking",
    title: "Rank the shortlist",
    detail: "Favor relevance first, then engagement.",
  },
  {
    node: "comment_generation",
    title: "Draft comment angles",
    detail: "Prepare two copy-ready comments for each ranked post.",
  },
] as const;

export function StreamDisplay({ events, isLoading }: StreamDisplayProps) {
  const completedNodes = new Set(events.map((event) => event.node));
  const latestMessage = events.at(-1)?.message;

  return (
    <Card className="border border-border/70 bg-card/90 backdrop-blur">
      <CardHeader>
        <div className="text-xs font-semibold tracking-[0.24em] text-muted-foreground uppercase">
          Step 2
        </div>
        <CardTitle className="flex items-center gap-2 text-2xl">
          Watch the run move
          {isLoading && (
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary" />
          )}
        </CardTitle>
        <CardDescription>
          Concise milestones only. Internal noise stays out of the way.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {steps.map((step, index) => {
            const isComplete = completedNodes.has(step.node);
            const isActive =
              isLoading && !isComplete && steps[index - 1]?.node
                ? completedNodes.has(steps[index - 1].node)
                : isLoading && index === 0 && events.length === 0;

            return (
              <div
                key={step.node}
                className="flex gap-3 rounded-xl border border-border/70 p-4"
              >
                <Badge
                  variant={isComplete ? "default" : "outline"}
                  className="mt-0.5 shrink-0"
                >
                  {isComplete ? "Done" : isActive ? "Now" : `0${index + 1}`}
                </Badge>
                <div className="space-y-1">
                  <div className="font-medium">{step.title}</div>
                  <p className="text-sm text-muted-foreground">{step.detail}</p>
                </div>
              </div>
            );
          })}

          <div
            aria-live="polite"
            className="rounded-xl border border-dashed border-border px-4 py-3 text-sm text-muted-foreground"
          >
            {latestMessage ||
              "Waiting for a run. Once submitted, milestone updates will land here."}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
