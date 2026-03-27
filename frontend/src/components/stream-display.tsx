"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { StreamEvent } from "@/lib/types";

interface StreamDisplayProps {
  events: StreamEvent[];
  isLoading: boolean;
}

const nodeLabels: Record<string, string> = {
  fetch_sources: "Fetching Sources",
  analyze_content: "Analyzing Content",
  generate_material: "Generating Material",
  evaluate_quality: "Evaluating Quality",
  complete: "Complete",
};

export function StreamDisplay({ events, isLoading }: StreamDisplayProps) {
  if (events.length === 0 && !isLoading) return null;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          Pipeline Progress
          {isLoading && (
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary" />
          )}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {events
            .filter((e) => e.event_type !== "result")
            .map((event, i) => (
              <div key={i} className="flex items-start gap-3">
                <Badge
                  variant={
                    event.event_type === "evaluation" ? "secondary" : "default"
                  }
                  className="mt-0.5 shrink-0"
                >
                  {nodeLabels[event.node] || event.node}
                </Badge>
                <span className="text-sm text-muted-foreground">
                  {event.message}
                </span>
                {event.event_type === "evaluation" && event.data && (
                  <div className="ml-auto flex gap-2 text-xs">
                    {typeof event.data.accuracy_score === "number" && (
                      <span>Acc: {(event.data.accuracy_score as number).toFixed(1)}</span>
                    )}
                    {typeof event.data.completeness_score === "number" && (
                      <span>
                        Comp: {(event.data.completeness_score as number).toFixed(1)}
                      </span>
                    )}
                    {typeof event.data.clarity_score === "number" && (
                      <span>
                        Clar: {(event.data.clarity_score as number).toFixed(1)}
                      </span>
                    )}
                  </div>
                )}
              </div>
            ))}
        </div>
      </CardContent>
    </Card>
  );
}
