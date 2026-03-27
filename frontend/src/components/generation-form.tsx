"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import type { SuggestionRequest, ToneProfile } from "@/lib/types";

interface GenerationFormProps {
  onSubmit: (request: SuggestionRequest) => void;
  isLoading: boolean;
}

const PERSONA_OPTIONS = [
  "Founder",
  "Consultant",
  "Operator",
  "Job seeker",
  "Custom",
] as const;

const TOPIC_OPTIONS = [
  "AI agents",
  "B2B SaaS growth",
  "Creator partnerships",
  "Product strategy",
  "Custom",
] as const;

const PERSONA_SUBTITLE =
  "Defines the role perspective we use for comment voice and examples.";

const PERSONA_GUIDANCE: Record<string, string> = {
  founder: "Founder mode: focuses on product, traction, and POV-based comments.",
  consultant:
    "Consultant mode: emphasizes frameworks, diagnosis, and practical recommendations.",
  operator:
    "Operator mode: prioritizes execution detail, process, and measurable outcomes.",
  "job seeker":
    "Job seeker mode: highlights learning mindset, curiosity, and relevant experience.",
  custom: "Custom mode: define your own role framing for more precise comment direction.",
};

const DEFAULT_TONE: ToneProfile = {
  professional_casual: 50,
  reserved_warm: 50,
  measured_bold: 50,
  conventional_fresh: 50,
};

const TONE_PRESETS: Array<{ label: string; values: ToneProfile }> = [
  { label: "Balanced", values: DEFAULT_TONE },
  {
    label: "Warm",
    values: {
      professional_casual: 62,
      reserved_warm: 76,
      measured_bold: 52,
      conventional_fresh: 56,
    },
  },
  {
    label: "Bold",
    values: {
      professional_casual: 57,
      reserved_warm: 58,
      measured_bold: 82,
      conventional_fresh: 70,
    },
  },
];

const TONE_FIELDS: Array<{
  key: keyof ToneProfile;
  label: string;
  leftLabel: string;
  rightLabel: string;
}> = [
  {
    key: "professional_casual",
    label: "Professional <-> Casual",
    leftLabel: "Professional",
    rightLabel: "Casual",
  },
  {
    key: "reserved_warm",
    label: "Reserved <-> Warm",
    leftLabel: "Reserved",
    rightLabel: "Warm",
  },
  {
    key: "measured_bold",
    label: "Measured <-> Bold",
    leftLabel: "Measured",
    rightLabel: "Bold",
  },
  {
    key: "conventional_fresh",
    label: "Conventional <-> Fresh",
    leftLabel: "Conventional",
    rightLabel: "Fresh",
  },
];

export function GenerationForm({ onSubmit, isLoading }: GenerationFormProps) {
  const [persona, setPersona] = useState("");
  const [customPersona, setCustomPersona] = useState("");
  const [topic, setTopic] = useState("");
  const [customTopic, setCustomTopic] = useState("");
  const [keywordInput, setKeywordInput] = useState("");
  const [keywords, setKeywords] = useState<string[]>([]);
  const [tone, setTone] = useState<ToneProfile>(DEFAULT_TONE);

  const resolvedPersona = useMemo(() => {
    if (persona.toLowerCase() === "custom") {
      return customPersona.trim();
    }
    return persona.trim();
  }, [customPersona, persona]);

  const resolvedTopic = useMemo(() => {
    if (topic.toLowerCase() === "custom") {
      return customTopic.trim();
    }
    return topic.trim();
  }, [customTopic, topic]);

  const canSubmit =
    !isLoading &&
    resolvedPersona.length > 0 &&
    resolvedTopic.length > 0 &&
    keywords.length > 0;

  const activePersonaGuidance = PERSONA_GUIDANCE[persona.toLowerCase()];

  const addKeyword = () => {
    const cleaned = keywordInput.trim();
    if (!cleaned) return;
    if (keywords.includes(cleaned)) {
      setKeywordInput("");
      return;
    }
    setKeywords((current) => [...current, cleaned]);
    setKeywordInput("");
  };

  const removeKeyword = (keyword: string) => {
    if (isLoading) return;
    setKeywords((current) => current.filter((item) => item !== keyword));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!canSubmit) return;

    onSubmit({
      persona: resolvedPersona,
      topic: resolvedTopic,
      keywords,
      tone,
    });
  };

  return (
    <Card className="border border-border/70 bg-card/90 backdrop-blur">
      <CardHeader>
        <div className="text-xs font-semibold tracking-[0.24em] text-muted-foreground uppercase">
          Step 1
        </div>
        <CardTitle className="text-2xl">Set your LinkedIn angle</CardTitle>
        <CardDescription>
          Choose who you are, what discussions to join, and how your comments
          should sound.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="persona" className="text-sm font-medium">
                Persona
              </label>
              <p className="text-xs text-muted-foreground">{PERSONA_SUBTITLE}</p>
              <select
                id="persona"
                value={persona.toLowerCase() === "custom" ? "custom" : persona}
                onChange={(e) => setPersona(e.target.value)}
                disabled={isLoading}
                className="h-11 w-full rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <option value="">Choose the closest fit</option>
                {PERSONA_OPTIONS.map((option) => (
                  <option
                    key={option}
                    value={option === "Custom" ? "custom" : option}
                  >
                    {option}
                  </option>
                ))}
              </select>
              {activePersonaGuidance && (
                <p className="text-xs text-muted-foreground">{activePersonaGuidance}</p>
              )}
              {persona === "custom" && (
                <div className="space-y-1">
                  <label htmlFor="custom-persona" className="text-xs text-muted-foreground">
                    Custom persona
                  </label>
                  <Input
                    id="custom-persona"
                    placeholder="e.g., Community-led founder"
                    value={customPersona}
                    onChange={(e) => setCustomPersona(e.target.value)}
                    disabled={isLoading}
                  />
                </div>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="topic" className="text-sm font-medium">
                Topic
              </label>
              <p className="text-xs text-muted-foreground">
                Defines which LinkedIn conversation lane we prioritize.
              </p>
              <select
                id="topic"
                value={topic.toLowerCase() === "custom" ? "custom" : topic}
                onChange={(e) => setTopic(e.target.value)}
                disabled={isLoading}
                className="h-11 w-full rounded-lg border border-input bg-transparent px-3 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50"
              >
                <option value="">Choose a conversation lane</option>
                {TOPIC_OPTIONS.map((option) => (
                  <option
                    key={option}
                    value={option === "Custom" ? "custom" : option}
                  >
                    {option}
                  </option>
                ))}
              </select>
              {topic === "custom" && (
                <div className="space-y-1">
                  <label htmlFor="custom-topic" className="text-xs text-muted-foreground">
                    Custom topic
                  </label>
                  <Input
                    id="custom-topic"
                    placeholder="e.g., AI pricing strategy for B2B SaaS"
                    value={customTopic}
                    onChange={(e) => setCustomTopic(e.target.value)}
                    disabled={isLoading}
                  />
                </div>
              )}
            </div>
          </div>

          <div className="space-y-3">
            <label htmlFor="keyword-input" className="text-sm font-medium">
              Keywords (include only)
            </label>
            <p className="text-xs text-muted-foreground">
              Add must-match words or short phrases to keep discovery focused.
            </p>
            <p className="text-xs text-muted-foreground">
              Keep keywords specific so discovery stays focused.
            </p>
            <div className="flex gap-2">
              <Input
                id="keyword-input"
                placeholder="e.g., product-market fit"
                value={keywordInput}
                onChange={(e) => setKeywordInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addKeyword();
                  }
                }}
                disabled={isLoading}
              />
              <Button type="button" variant="outline" onClick={addKeyword} disabled={isLoading}>
                Add keyword
              </Button>
            </div>
            <div className="flex flex-wrap gap-2">
              {keywords.map((keyword) => (
                <button
                  key={keyword}
                  type="button"
                  onClick={() => removeKeyword(keyword)}
                  disabled={isLoading}
                  aria-disabled={isLoading}
                  className="rounded-full border border-border px-3 py-1 text-sm text-muted-foreground transition hover:border-foreground hover:text-foreground disabled:cursor-not-allowed disabled:opacity-50 disabled:hover:border-border disabled:hover:text-muted-foreground"
                >
                  {keyword} x
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-medium">Tone controls</div>
              <div className="flex flex-wrap gap-2">
                {TONE_PRESETS.map((preset) => (
                  <Button
                    key={preset.label}
                    type="button"
                    size="sm"
                    variant="outline"
                    disabled={isLoading}
                    onClick={() => setTone(preset.values)}
                  >
                    {preset.label}
                  </Button>
                ))}
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              Each slider balances two writing styles of your comments. Start
              with a preset, then fine-tune.
            </p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {TONE_FIELDS.map((field) => (
              <div key={field.key} className="rounded-xl border border-border/70 p-4">
                <div className="space-y-2">
                  <label
                    htmlFor={field.key}
                    className="text-sm font-medium"
                  >
                    {field.label}
                  </label>
                  <input
                    id={field.key}
                    type="range"
                    min={0}
                    max={100}
                    step={1}
                    value={tone[field.key]}
                    onChange={(e) =>
                      setTone((current) => ({
                        ...current,
                        [field.key]: Number(e.target.value),
                      }))
                    }
                    disabled={isLoading}
                    className="w-full accent-foreground"
                  />
                </div>
                <div className="mt-2 flex items-center justify-between text-xs text-muted-foreground">
                  <span>{field.leftLabel}</span>
                  <span>
                    {tone[field.key] < 35
                      ? `Leaning ${field.leftLabel}`
                      : tone[field.key] > 65
                        ? `Leaning ${field.rightLabel}`
                        : "Balanced"}
                  </span>
                  <span>{field.rightLabel}</span>
                </div>
              </div>
            ))}
          </div>

          <Button type="submit" className="h-11 w-full" disabled={!canSubmit}>
            {isLoading ? "Preparing..." : "Find posts to comment on"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
