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

const FULL_TEXT_PREVIEW_CHAR_LIMIT = 2000;

export function ResultDisplay({ result }: ResultDisplayProps) {
  const [expandedPostUrl, setExpandedPostUrl] = useState<string | null>(null);
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

  const togglePostExpansion = (postUrl: string) => {
    setExpandedPostUrl((previous) => (previous === postUrl ? null : postUrl));
    setRevealedRestByPost((previous) => ({ ...previous, [postUrl]: false }));
  };

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
        const isExpanded = expandedPostUrl === post.post_url;
        const fullTextSource = post.full_text.trimStart();
        const trimmedPreview = post.preview.trim();
        const dedupedCandidate = fullTextSource.startsWith(trimmedPreview)
          ? fullTextSource.slice(trimmedPreview.length).trimStart()
          : post.full_text;
        const dedupedFullText = dedupedCandidate.length > 0 ? dedupedCandidate : post.full_text;
        const isLongText = dedupedFullText.length > FULL_TEXT_PREVIEW_CHAR_LIMIT;
        const hasRevealedRest = Boolean(revealedRestByPost[post.post_url]);
        const fullTextPreview = isLongText
          ? `${dedupedFullText.slice(0, FULL_TEXT_PREVIEW_CHAR_LIMIT).trimEnd()}...`
          : dedupedFullText;
        const displayedFullText =
          isLongText && !hasRevealedRest ? fullTextPreview : dedupedFullText;

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
                <p className="text-sm leading-6 text-foreground/90">{post.preview}</p>
                <div className="flex flex-wrap items-center gap-3">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    aria-label={
                      isExpanded
                        ? `Hide full post for ${post.author}`
                        : `Show full post for ${post.author}`
                    }
                    aria-expanded={isExpanded}
                    aria-controls={`full-post-${post.rank}`}
                    onClick={() => togglePostExpansion(post.post_url)}
                  >
                    {isExpanded ? "Hide full post" : "Show more"}
                  </Button>
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

              {isExpanded && (
                <div
                  id={`full-post-${post.rank}`}
                  className="rounded-xl border border-border/70 bg-muted/20 p-4"
                >
                  <div className="text-xs font-semibold tracking-[0.2em] text-muted-foreground uppercase">
                    Full post continuation
                  </div>
                  <p className="mt-2 text-sm leading-6 text-foreground/90">
                    {displayedFullText}
                  </p>
                  {isLongText && !hasRevealedRest && (
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="mt-2"
                      aria-label={`Show rest of full text for ${post.author}`}
                      onClick={() => revealRest(post.post_url)}
                    >
                      See more
                    </Button>
                  )}
                </div>
              )}

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
                className="flex snap-x snap-mandatory gap-3 overflow-x-auto pb-1 md:grid md:grid-cols-2 md:overflow-visible md:pb-0"
              >
                {post.suggested_comments.map((comment, index) => (
                  <div
                    key={comment.id}
                    className="min-w-[84%] snap-start rounded-xl border border-border/70 p-4 md:min-w-0"
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
