"use client";

import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import type { SuggestionResult } from "@/lib/types";

interface ResultDisplayProps {
  result: SuggestionResult | null;
}

export function ResultDisplay({ result }: ResultDisplayProps) {
  if (!result) return null;

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <Badge variant="outline">3 ranked post opportunities</Badge>
        {result.partial && <Badge variant="secondary">Partial result</Badge>}
        <span className="text-sm text-muted-foreground">
          {result.request_summary}
        </span>
      </div>

      {result.partial && result.recovery_message && (
        <div className="rounded-xl border border-amber-300/50 bg-amber-100/40 p-4 text-sm text-amber-950">
          {result.recovery_message}
        </div>
      )}

      {result.posts.map((post) => (
        <Card
          key={post.post_url}
          className="border border-border/70 bg-card/90 backdrop-blur"
        >
          <CardHeader>
            <div className="flex flex-wrap items-center gap-2">
              <Badge>Rank #{post.rank}</Badge>
              <Badge variant="outline">{post.engagement.reactions} reactions</Badge>
              <Badge variant="outline">{post.engagement.comments} comments</Badge>
            </div>
            <CardTitle className="text-xl">{post.author}</CardTitle>
            <CardDescription>{post.author_headline}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-5">
            <div className="space-y-2">
              <div className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                Post preview
              </div>
              <p className="text-sm leading-6 text-foreground/90">{post.preview}</p>
              <a
                href={post.post_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex text-sm font-medium text-foreground underline underline-offset-4"
              >
                Open post on LinkedIn
              </a>
            </div>

            <div className="rounded-xl border border-border/70 bg-muted/30 p-4">
              <div className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                Why it ranked
              </div>
              <p className="mt-2 text-sm leading-6 text-foreground/90">
                {post.rationale}
              </p>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {post.suggested_comments.map((comment, index) => (
                <div
                  key={comment.id}
                  className="rounded-xl border border-border/70 p-4"
                >
                  <div className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                    Comment option {index + 1}
                  </div>
                  <p className="mt-2 text-sm leading-6 text-foreground/90">
                    {comment.text}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
