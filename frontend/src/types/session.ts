export type WizardStage = "concept" | "quiz" | "editor" | "grade" | "done";

export type Topic = {
  chapter: string;
  concept: string;
};

export type SyntaxForm = {
  label: string;
  code: string;
};

export type ConceptReview = {
  definition: string;
  how_it_works: string[];
  syntax_forms: SyntaxForm[];
  worked_example_code: string;
  worked_example_walkthrough: string[];
  common_patterns: string[];
  analogy: string;
  gotcha: string;
  when_to_use: string;
};

export type Question =
  | {
      type: "mc";
      subtype: "multiple_choice" | "what_does_this_print";
      text: string;
      code?: string;
      options: string[];
      correct_index: number | null;
    }
  | {
      type: "free";
      subtype: "short_answer" | "stretch_conceptual";
      text: string;
    };

export type Exercise = {
  topic: string;
  task: string;
  expected_output: string;
  constraints: string[];
};

export type ApplyAtWork = {
  angle: string;
  text: string;
};

/** Inner shape of a generated session — returned inside `SessionResponse`. */
export type SessionData = {
  topic: Topic;
  concept_review: ConceptReview;
  questions: Question[];
};

/** Backend signal that today already has a logged session and the user must
 * choose whether to review the same chapter or advance to the next one. */
export type NeedsIntent = {
  kind: "needs_intent";
  today_chapter: string;
  today_concept: string;
};

/** Discriminated union returned by POST /session/start. */
export type StartResponse =
  | ({ kind: "session" } & SessionData)
  | NeedsIntent;

/** Intent the frontend can pass to /session/start to resolve a needs_intent. */
export type StartIntent = "advance" | "review";

/** One past chapter returned by GET /chapters/done. */
export type DoneChapter = {
  chapter: string;
  last_date: string;
};

/** Returned by GET /chapters/done. */
export type DoneChaptersResponse = {
  chapters: DoneChapter[];
};

/** Returned by POST /session/exercise. */
export type ExerciseResult = {
  exercise: Exercise;
  apply_at_work: ApplyAtWork;
  angle: string;
  exercise_text: string;
};

/** Returned by POST /session/grade. */
export type GradeResult = {
  grade_markdown: string;
  score_correct: number;
  score_total: number;
};

/** Returned by POST /session/review. */
export type ReviewResult = {
  review_markdown: string;
  verdict: "pass" | "close" | "miss";
  reference_solution?: string;
};

/** Returned by POST /session/log. */
export type LogResult = {
  ok: boolean;
  exercise_path: string;
  progress_path: string;
};

/** Loading / error UI state. */
export type Status =
  | { kind: "idle" }
  | { kind: "loading"; what: string }
  | { kind: "error"; message: string };

/** Free-form mentor-chat conversation turn. */
export type ChatRole = "user" | "mentor";
export type ChatMessage = { role: ChatRole; text: string };

/** Payload for POST /session/ask. */
export type AskPayload = {
  question: string;
  chapter: string;
  concept: string;
  stage: WizardStage;
  history: ChatMessage[];
};

/** Returned by POST /session/ask. */
export type AskResult = {
  answer: string;
  provider: string;
};
