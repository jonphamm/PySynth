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

/** Returned by POST /session/start. */
export type SessionData = {
  topic: Topic;
  concept_review: ConceptReview;
  questions: Question[];
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
