"use client";

import { GenerationForm } from "@/components/generation-form";
import { ResultDisplay } from "@/components/result-display";
import { StreamDisplay } from "@/components/stream-display";
import { Button } from "@/components/ui/button";
import { useGenerationStream } from "@/hooks/use-generation-stream";

export default function Home() {
  const { events, result, isLoading, error, generate, reset } =
    useGenerationStream();

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.9),_rgba(242,238,232,0.82)_38%,_rgba(232,226,216,0.72)_100%)]">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-10 md:px-8 md:py-14">
        <header className="grid gap-6 lg:grid-cols-[1.4fr_0.8fr] lg:items-end">
          <div className="space-y-4">
            <div className="text-xs font-semibold tracking-[0.28em] text-muted-foreground uppercase">
              LinkedIn visibility MVP
            </div>
            <h1 className="max-w-4xl text-5xl leading-tight font-medium tracking-tight text-foreground md:text-6xl">
              Find public LinkedIn posts worth commenting on, then leave with two
              ready-to-use replies for each.
            </h1>
            <p className="max-w-2xl text-base leading-7 text-muted-foreground md:text-lg">
              This flow is intentionally narrow: shape the request, watch the run,
              and review three ranked opportunities without turning the product
              into a noisy dashboard.
            </p>
          </div>

          <div className="rounded-2xl border border-border/70 bg-card/80 p-5 backdrop-blur">
            <div className="text-xs font-semibold tracking-[0.24em] text-muted-foreground uppercase">
              Three-step run
            </div>
            <div className="mt-3 space-y-3 text-sm">
              <div className="flex items-center justify-between border-b border-border/70 pb-3">
                <span>01 Input</span>
                <span className="text-muted-foreground">persona, topic, keywords, tone</span>
              </div>
              <div className="flex items-center justify-between border-b border-border/70 pb-3">
                <span>02 Progress</span>
                <span className="text-muted-foreground">concise milestones only</span>
              </div>
              <div className="flex items-center justify-between">
                <span>03 Output</span>
                <span className="text-muted-foreground">ranked posts + 2 comments each</span>
              </div>
            </div>
          </div>
        </header>

        <section>
          <GenerationForm onSubmit={generate} isLoading={isLoading} />
        </section>

        <section>
          <StreamDisplay events={events} isLoading={isLoading} />
        </section>

        {error && (
          <div className="rounded-2xl border border-destructive/30 bg-destructive/5 p-4 text-sm text-destructive">
            {error}
          </div>
        )}

        <section className="space-y-4">
          <div className="space-y-2">
            <div className="text-xs font-semibold tracking-[0.24em] text-muted-foreground uppercase">
              Step 3
            </div>
            <h2 className="text-3xl font-medium">Review ranked opportunities</h2>
            <p className="text-sm text-muted-foreground">
              Results stay in card form so you can scan the ranking logic and copy
              a draft without parsing raw payloads.
            </p>
          </div>

          <ResultDisplay result={result} />
        </section>

        {(result || error || events.length > 0) && (
          <div className="flex justify-end">
            <Button variant="outline" onClick={reset}>
              Clear current run
            </Button>
          </div>
        )}
      </div>
    </main>
  );
}
