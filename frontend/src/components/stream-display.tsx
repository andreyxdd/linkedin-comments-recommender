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
    title: "Discover relevant posts",
    detail: "Search public LinkedIn conversations worth a closer look.",
  },
  {
    title: "Score the shortlist",
    detail: "Rank the strongest matches before drafting comments.",
  },
  {
    title: "Prepare final suggestions",
    detail: "Package the top opportunities with two ready-to-use replies each.",
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
  input: "Getting discovery ready",
  discovery: "Discovering relevant LinkedIn posts",
  ranking: "Scoring the strongest matches",
  comment_generation: "Preparing your final suggestions",
  complete: "Final suggestions are ready to review.",
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
              "Waiting for a run. Once submitted, milestone updates will land here."}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
