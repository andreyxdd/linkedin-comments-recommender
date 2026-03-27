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

const milestones = [
  {
    title: "Find relevant posts",
    detail: "Scan public LinkedIn conversations worth attention.",
  },
  {
    title: "Rank the shortlist",
    detail: "Score the strongest matches before drafting comments.",
  },
  {
    title: "Draft comments",
    detail: "Prepare two ready replies for each top opportunity.",
  },
] as const;

const milestoneIndexByNode: Record<string, number> = {
  input: 0,
  discovery: 0,
  ranking: 1,
  comment_generation: 2,
  complete: 2,
};

const statusLabelByNode: Record<string, string> = {
  input: "Preparing discovery",
  discovery: "Finding relevant LinkedIn posts",
  ranking: "Ranking top matches",
  comment_generation: "Drafting final suggestions",
  complete: "Suggestions ready to review.",
};

export function StreamDisplay({ events, isLoading }: StreamDisplayProps) {
  const latestStatusEvent = [...events]
    .reverse()
    .find((event) => event.event_type === "status");
  const activeMilestoneIndex =
    latestStatusEvent?.node && latestStatusEvent.node in milestoneIndexByNode
      ? milestoneIndexByNode[latestStatusEvent.node]
      : null;
  const hasResult = events.some((event) => event.event_type === "result");
  const latestEvent = events.at(-1);
  const latestMessage = latestEvent
    ? statusLabelByNode[latestEvent.node] ?? "Working through the next milestone."
    : null;

  return (
    <Card className="border border-border/70 bg-card/90 backdrop-blur">
      <CardHeader>
        <div className="text-xs font-semibold tracking-[0.24em] text-muted-foreground uppercase">
          Step 2
        </div>
        <CardTitle className="flex items-center gap-2 text-2xl">
          Track the run
          {isLoading && (
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary" />
          )}
        </CardTitle>
        <CardDescription>
          Milestones only. Internal noise stays out.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {milestones.map((step, index) => {
            const isComplete =
              hasResult ||
              (activeMilestoneIndex !== null && index < activeMilestoneIndex);
            const isActive = isLoading
              ? activeMilestoneIndex === null
                ? index === 0
                : index === activeMilestoneIndex && !hasResult
              : false;

            return (
              <div
                key={step.title}
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
              "Waiting for a run. Milestone updates appear here."}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
