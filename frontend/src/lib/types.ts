export type OutputFormat = "summary" | "flashcards" | "quiz";
export type DifficultyLevel = "beginner" | "intermediate" | "advanced";

export interface GenerationRequest {
  topic: string;
  context: string;
  output_format: OutputFormat;
  difficulty: DifficultyLevel;
}

export interface DraftEvaluation {
  accuracy_score: number;
  completeness_score: number;
  clarity_score: number;
  passed: boolean;
  reasoning: string;
}

export interface DraftOutput {
  content: string;
  evaluation: DraftEvaluation | null;
}

export interface GenerationResult {
  drafts: DraftOutput[];
  iterations: number;
  sources_used: number;
}

export interface StreamEvent {
  event_type: "status" | "evaluation" | "result";
  node: string;
  message: string;
  data: Record<string, unknown>;
}
