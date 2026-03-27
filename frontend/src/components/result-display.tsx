"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { GenerationResult } from "@/lib/types";

interface ResultDisplayProps {
  result: GenerationResult | null;
}

export function ResultDisplay({ result }: ResultDisplayProps) {
  if (!result) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-4 text-sm text-muted-foreground">
        <span>Iterations: {result.iterations}</span>
        <span>Sources used: {result.sources_used}</span>
      </div>

      {result.drafts.map((draft, i) => (
        <Card key={i}>
          <CardHeader>
            <CardTitle className="text-lg">
              {result.drafts.length > 1 ? `Draft ${i + 1}` : "Result"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm max-w-none dark:prose-invert whitespace-pre-wrap">
              {draft.content}
            </div>
            {draft.evaluation && (
              <div className="mt-4 rounded-md border p-3 text-sm">
                <div className="mb-1 font-medium">Quality Scores</div>
                <div className="grid grid-cols-3 gap-2 text-muted-foreground">
                  <span>Accuracy: {draft.evaluation.accuracy_score.toFixed(2)}</span>
                  <span>
                    Completeness: {draft.evaluation.completeness_score.toFixed(2)}
                  </span>
                  <span>Clarity: {draft.evaluation.clarity_score.toFixed(2)}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
