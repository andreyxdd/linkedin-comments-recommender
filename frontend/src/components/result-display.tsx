"use client";

import { useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
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
  const [revealedRestByPost, setRevealedRestByPost] = useState<
    Record<string, boolean>
  >({});
  const [copiedCommentId, setCopiedCommentId] = useState<string | null>(null);
  const [copyFeedback, setCopyFeedback] = useState<string | null>(null);

  useEffect(() => {
    if (!copyFeedback) return;
    const timer = window.setTimeout(() => {
      setCopyFeedback(null);
      setCopiedCommentId(null);
    }, 2000);
    return () => window.clearTimeout(timer);
  }, [copyFeedback]);

  if (!result) return null;

  const revealRest = (postUrl: string) => {
    setRevealedRestByPost((previous) => ({ ...previous, [postUrl]: true }));
  };

  const copyComment = async (commentId: string, commentText: string) => {
    try {
      await navigator.clipboard.writeText(commentText);
      setCopiedCommentId(commentId);
      setCopyFeedback("Comment copied to clipboard.");
      return;
    } catch {
      setCopiedCommentId(null);
      setCopyFeedback("Unable to copy comment.");
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <Badge variant="outline">3 ranked posts</Badge>
        {result.partial && <Badge variant="secondary">Partial</Badge>}
        <span className="text-sm text-muted-foreground">
          {result.request_summary}
        </span>
      </div>
      {copyFeedback && (
        <div
          role="status"
          aria-live="polite"
          className="fixed right-4 bottom-4 z-50 rounded-lg border border-border/70 bg-card px-3 py-2 text-sm text-foreground shadow-sm"
        >
          {copyFeedback}
        </div>
      )}

      {result.partial && result.recovery_message && (
        <div className="rounded-xl border border-amber-300/50 bg-amber-100/40 p-4 text-sm text-amber-950">
          {result.recovery_message}
        </div>
      )}

      {result.posts.map((post) => {
        const previewText = post.preview.trimEnd();
        const fullTextSource = post.full_text.trimStart();
        const continuationText = fullTextSource.startsWith(previewText)
          ? fullTextSource.slice(previewText.length)
          : "";
        const hasContinuation =
          continuationText.trim().length > 0 && continuationText.length > 0;
        const hasRevealedRest = Boolean(revealedRestByPost[post.post_url]);

        return (
          <Card
            key={post.post_url}
            className="border border-border/70 bg-card/90 backdrop-blur"
          >
            <CardHeader>
              <div className="flex flex-wrap items-center gap-2">
                <Badge>Rank #{post.rank}</Badge>
                <Badge variant="outline" className="border-sky-300/70 bg-sky-100/80 text-sky-900">
                  {post.engagement.reactions} reactions
                </Badge>
                <Badge
                  variant="outline"
                  className="border-emerald-300/70 bg-emerald-100/80 text-emerald-900"
                >
                  {post.engagement.comments} comments
                </Badge>
              </div>
              <CardTitle className="text-xl">{post.author}</CardTitle>
              <CardDescription>{post.author_headline}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-5">
              <div className="space-y-2">
                <div className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                  Preview
                </div>
                <p
                  id={`full-post-${post.rank}`}
                  className="text-sm leading-6 text-foreground/90 whitespace-pre-wrap"
                >
                  {previewText}
                  {hasContinuation && !hasRevealedRest && (
                    <>
                      {" "}
                      <button
                        type="button"
                        aria-label={`See more post text for ${post.author}`}
                        onClick={() => revealRest(post.post_url)}
                        className="inline font-medium text-foreground underline underline-offset-4"
                      >
                        See more...
                      </button>
                    </>
                  )}
                  {hasContinuation && hasRevealedRest && continuationText}
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <a
                    href={post.post_url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex text-sm font-medium text-foreground underline underline-offset-4"
                  >
                    Open on LinkedIn
                  </a>
                </div>
              </div>

              <div className="rounded-xl border border-border/70 bg-muted/30 p-4">
                <div className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                  Why this ranked
                </div>
                <p className="mt-2 text-sm leading-6 text-foreground/90">
                  {post.rationale}
                </p>
              </div>

              <div
                data-testid="comment-options-row"
                className="flex snap-x snap-mandatory gap-3 overflow-x-auto pb-1"
              >
                {post.suggested_comments.map((comment, index) => (
                  <div
                    key={comment.id}
                    className="min-w-[18rem] max-w-[26rem] snap-start rounded-xl border border-border/70 p-4"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                        Option {index + 1}
                      </div>
                      <Button
                        type="button"
                        size="xs"
                        variant={copiedCommentId === comment.id ? "secondary" : "outline"}
                        aria-label={
                          copiedCommentId === comment.id
                            ? `Copied option ${index + 1} for ${post.author}`
                            : `Copy option ${index + 1} for ${post.author}`
                        }
                        onClick={() =>
                          copyComment(comment.id, comment.text)
                        }
                      >
                        {copiedCommentId === comment.id ? "Copied" : "Copy"}
                      </Button>
                    </div>
                    <p className="mt-2 text-sm leading-6 text-foreground/90">
                      {comment.text}
                    </p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
