"use client";

import { useCallback, useRef, useState } from "react";

import { getApiUrl } from "@/lib/api";
import type {
  SuggestionRequest,
  SuggestionResult,
  StreamEvent,
} from "@/lib/types";

interface UseGenerationStreamReturn {
  events: StreamEvent[];
  result: SuggestionResult | null;
  isLoading: boolean;
  error: string | null;
  generate: (request: SuggestionRequest) => void;
  reset: () => void;
}

export function useGenerationStream(): UseGenerationStreamReturn {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [result, setResult] = useState<SuggestionResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    setEvents([]);
    setResult(null);
    setIsLoading(false);
    setError(null);
  }, []);

  const generate = useCallback((request: SuggestionRequest) => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setEvents([]);
    setResult(null);
    setIsLoading(true);
    setError(null);

    (async () => {
      try {
        const response = await fetch(getApiUrl("/api/generate"), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(request),
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error(
            "We couldn't complete this run. Please try again in a moment.",
          );
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          let currentEventType = "";
          for (const line of lines) {
            if (line.startsWith("event: ")) {
              currentEventType = line.slice(7).trim();
            } else if (line.startsWith("data: ")) {
              const data = line.slice(6);
              try {
                const parsed: StreamEvent = JSON.parse(data);
                setEvents((prev) => [...prev, parsed]);

                if (
                  currentEventType === "result" ||
                  parsed.event_type === "result"
                ) {
                  setResult(parsed.data as unknown as SuggestionResult);
                }
              } catch {
                // Skip malformed JSON
              }
            }
          }
        }
      } catch (err) {
        if (err instanceof Error && err.name !== "AbortError") {
          if (err.message.includes("Failed to fetch")) {
            setError("Unable to reach the service. Check connection and retry.");
          } else {
            setError(err.message);
          }
        }
      } finally {
        setIsLoading(false);
      }
    })();
  }, []);

  return { events, result, isLoading, error, generate, reset };
}
