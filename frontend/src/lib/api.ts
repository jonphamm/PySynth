import type {
  AskPayload,
  AskResult,
  DoneChaptersResponse,
  ExerciseResult,
  GradeResult,
  LogResult,
  ReviewResult,
  StartIntent,
  StartResponse,
  Topic,
  Exercise,
  Question,
} from "@/types/session";
import { getOrCreateUserId } from "./userId";

const BASE =
  process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  init: RequestInit,
): Promise<T> {
  const userId = getOrCreateUserId();
  const headers = new Headers(init.headers);
  if (userId) headers.set("X-User-Id", userId);
  let res: Response;
  try {
    res = await fetch(`${BASE}${path}`, { ...init, headers });
  } catch (err) {
    throw new ApiError(0, `Cannot reach backend at ${BASE} — is it running?`);
  }
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const data = await res.json();
      if (data?.detail) detail = String(data.detail);
    } catch {
      /* swallow */
    }
    throw new ApiError(res.status, detail);
  }
  return (await res.json()) as T;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: "GET" });
}

export type StartOptions = {
  intent?: StartIntent;
  pinChapter?: string;
};

export function startSession(opts: StartOptions = {}): Promise<StartResponse> {
  const body: Record<string, unknown> = {};
  if (opts.intent) body.intent = opts.intent;
  if (opts.pinChapter) body.pin_to_chapter = opts.pinChapter;
  return post<StartResponse>("/session/start", body);
}

export function listDoneChapters(): Promise<DoneChaptersResponse> {
  return get<DoneChaptersResponse>("/chapters/done");
}

export type GradePayload = {
  questions: Question[];
  answers: string[];
  picked_indexes: (number | null)[];
};

export function gradeQuiz(payload: GradePayload): Promise<GradeResult> {
  return post<GradeResult>("/session/grade", payload);
}

export type ExercisePayload = {
  topic: Topic;
  concept: string;
};

export function generateExercise(
  payload: ExercisePayload
): Promise<ExerciseResult> {
  return post<ExerciseResult>("/session/exercise", payload);
}

export type ReviewPayload = {
  exercise: Exercise;
  code: string;
};

export function reviewCode(payload: ReviewPayload): Promise<ReviewResult> {
  return post<ReviewResult>("/session/review", payload);
}

export type LogPayload = {
  chapter: string;
  topic: string;
  quiz_score: string;
  exercise_verdict: string;
  apply_summary: string;
  angle: string;
  feeling: string;
  code: string;
  exercise_text: string;
  type?: string;
};

export function logSession(payload: LogPayload): Promise<LogResult> {
  return post<LogResult>("/session/log", payload);
}

export function askMentor(payload: AskPayload): Promise<AskResult> {
  return post<AskResult>("/session/ask", payload);
}

export { ApiError };
