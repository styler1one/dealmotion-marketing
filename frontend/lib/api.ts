/**
 * API client for DealMotion Marketing Engine backend
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface ApiOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  body?: unknown;
}

async function api<T>(endpoint: string, options: ApiOptions = {}): Promise<T> {
  const { method = "GET", body } = options;

  const response = await fetch(`${API_URL}${endpoint}`, {
    method,
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(error.detail || `API error: ${response.status}`);
  }

  return response.json();
}

// ============================================================
// Topics
// ============================================================

export interface Topic {
  id: string;
  content_type: string;
  title: string;
  hook: string;
  main_points: string[];
  cta: string;
  hashtags: string[];
  estimated_duration_seconds: number;
}

export interface GenerateTopicsRequest {
  content_type?: string;
  count?: number;
  language?: string;
}

export async function generateTopics(request: GenerateTopicsRequest = {}) {
  return api<{ topics: Topic[]; count: number }>("/api/topics/generate", {
    method: "POST",
    body: request,
  });
}

export async function getContentTypes() {
  return api<{ types: { id: string; name: string }[] }>("/api/topics/types");
}

// ============================================================
// Scripts
// ============================================================

export interface Script {
  id: string;
  topic_id: string;
  title: string;
  description: string;
  segments: { text: string; duration: number }[];
  full_text: string;
  total_duration_seconds: number;
}

export interface GenerateScriptRequest {
  topic: Topic;
}

export async function generateScript(request: GenerateScriptRequest) {
  return api<Script>("/api/scripts/generate", {
    method: "POST",
    body: request,
  });
}

// ============================================================
// Pipeline
// ============================================================

export interface PipelineRun {
  id: string;
  run_date: string;
  status: "running" | "completed" | "failed" | "queued";
  current_step: number;
  steps: PipelineStep[];
}

export interface PipelineStep {
  step_number: number;
  step_name: string;
  status: "pending" | "running" | "completed" | "failed";
  output?: Record<string, unknown>;
  error?: string;
}

export async function getTodayPipeline() {
  return api<PipelineRun | null>("/api/pipeline/today");
}

export async function triggerPipeline() {
  return api<{ run_id: string; message: string }>("/api/pipeline/trigger", {
    method: "POST",
  });
}

// ============================================================
// Health
// ============================================================

export async function checkHealth() {
  return api<{ status: string; inngest: string; database: string }>("/health");
}

