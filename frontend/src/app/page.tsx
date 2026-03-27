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
    <div className="mx-auto flex w-full max-w-3xl flex-1 flex-col gap-6 px-4 py-8">
      <header>
        <h1 className="text-2xl font-bold">AI Agentic Loop</h1>
        <p className="text-muted-foreground">
          Fetch, analyze, generate, and evaluate — powered by LangGraph
        </p>
      </header>

      <GenerationForm onSubmit={generate} isLoading={isLoading} />
      <StreamDisplay events={events} isLoading={isLoading} />

      {error && (
        <div className="rounded-md border border-destructive p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      <ResultDisplay result={result} />

      {result && (
        <Button variant="outline" onClick={reset}>
          Start Over
        </Button>
      )}
    </div>
  );
}
