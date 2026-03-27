export interface ToneProfile {
  professional_casual: number;
  reserved_warm: number;
  measured_bold: number;
  conventional_fresh: number;
}

export interface SuggestionRequest {
  persona: string;
  topic: string;
  keywords: string[];
  tone: ToneProfile;
}

export interface PostEngagement {
  reactions: number;
  comments: number;
}

export interface SuggestedComment {
  id: string;
  text: string;
}

export interface RankedPost {
  rank: number;
  author: string;
  author_headline: string;
  post_url: string;
  preview: string;
  rationale: string;
  engagement: PostEngagement;
  suggested_comments: SuggestedComment[];
}

export interface SuggestionResult {
  posts: RankedPost[];
  partial: boolean;
  request_summary: string;
}

export interface StreamEvent {
  event_type: "status" | "result";
  node: string;
  message: string;
  data: Record<string, unknown>;
}
