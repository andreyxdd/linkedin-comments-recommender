"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type {
  DifficultyLevel,
  GenerationRequest,
  OutputFormat,
} from "@/lib/types";

interface GenerationFormProps {
  onSubmit: (request: GenerationRequest) => void;
  isLoading: boolean;
}

export function GenerationForm({ onSubmit, isLoading }: GenerationFormProps) {
  const [topic, setTopic] = useState("");
  const [context, setContext] = useState("");
  const [outputFormat, setOutputFormat] = useState<OutputFormat>("summary");
  const [difficulty, setDifficulty] = useState<DifficultyLevel>("intermediate");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!topic.trim()) return;
    onSubmit({
      topic: topic.trim(),
      context: context.trim() || "general",
      output_format: outputFormat,
      difficulty,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generate Content</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="topic" className="text-sm font-medium">
              Topic
            </label>
            <Input
              id="topic"
              placeholder="e.g., Photosynthesis, Machine Learning, Roman Empire"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="context" className="text-sm font-medium">
              Context / Field
            </label>
            <Input
              id="context"
              placeholder="e.g., biology, computer science, history (optional)"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              disabled={isLoading}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Output Format</label>
              <Select
                value={outputFormat}
                onValueChange={(v) => setOutputFormat(v as OutputFormat)}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="summary">Summary</SelectItem>
                  <SelectItem value="flashcards">Flashcards</SelectItem>
                  <SelectItem value="quiz">Quiz</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Difficulty</label>
              <Select
                value={difficulty}
                onValueChange={(v) => setDifficulty(v as DifficultyLevel)}
                disabled={isLoading}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="beginner">Beginner</SelectItem>
                  <SelectItem value="intermediate">Intermediate</SelectItem>
                  <SelectItem value="advanced">Advanced</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <Button type="submit" className="w-full" disabled={isLoading || !topic.trim()}>
            {isLoading ? "Generating..." : "Generate"}
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
