import type { ExerciseResult, SessionData } from "@/types/session";

/**
 * Frozen snapshot of LLM output, used as a visual-design sandbox when the
 * backend is unreachable. Nothing imports this in the live data flow — the
 * real session comes from `lib/api.ts`.
 */
export const mockSession: SessionData = {
  topic: {
    chapter: "Part 1: Chapter 4",
    concept: "Arithmetic Operations",
  },
  concept_review: {
    definition:
      "Arithmetic operators perform numeric calculations on int and float values. Python provides +, -, *, / (true division), // (floor division), % (modulo), and ** (exponentiation), each returning a numeric result whose type depends on the operands.",
    how_it_works: [
      "Operators are evaluated left-to-right with standard precedence: ** highest, then unary -, then *, /, //, %, then +, -.",
      "/ always returns a float; // returns int when both operands are int, float otherwise.",
      "% returns the remainder with the sign of the divisor for ints.",
      "Mixing int and float promotes the result to float silently.",
      "Parentheses override precedence and improve readability.",
    ],
    syntax_forms: [
      { label: "Basic operators", code: "total = price * quantity + tax" },
      { label: "Floor + modulo", code: "minutes, seconds = total // 60, total % 60" },
      { label: "Exponent", code: "energy = mass * c ** 2" },
      { label: "Augmented assignment", code: "count += 1" },
    ],
    worked_example_code:
      "# Convert 5025 seconds into a sysadmin-friendly format\ntotal_seconds = 5025\nhours = total_seconds // 3600\nremainder = total_seconds % 3600\nminutes = remainder // 60\nseconds = remainder % 60\nprint(f'{hours:02}:{minutes:02}:{seconds:02}')",
    worked_example_walkthrough: [
      "total_seconds = 5025 stores the input.",
      "// 3600 yields 1 (whole hours).",
      "% 3600 yields 1425 (remaining seconds).",
      "1425 // 60 yields 23 minutes; 1425 % 60 yields 45 seconds.",
      "The f-string prints '01:23:45' — a clean HH:MM:SS line for a log.",
    ],
    common_patterns: [
      "Use // when you need an integer count (pages, batches, full hours).",
      "Use % to detect divisibility: `if n % 2 == 0` is the canonical even-check.",
      "Reach for ** before importing math.pow — it's faster and more idiomatic.",
      "Augmented operators (+= -= *=) make accumulators read cleanly.",
    ],
    analogy:
      "Think of // and % like splitting bytes into kilobytes plus a leftover: `kb = bytes // 1024; rem = bytes % 1024`. They're how you turn a flat number into a structured report.",
    gotcha:
      "5 / 2 returns 2.5, not 2. If you want the integer half, use 5 // 2. Mixing this up is one of the most common Python beginner bugs.",
    when_to_use:
      "Reach for these any time you're transforming numeric data — counters, rates, conversions. If you find yourself writing a manual loop to count divisions, you almost certainly want // or %.",
  },
  questions: [
    {
      type: "mc",
      subtype: "multiple_choice",
      text: "Which operator returns the integer (floor) division result?",
      options: ["/", "//", "%", "**"],
      correct_index: 1,
    },
    {
      type: "mc",
      subtype: "what_does_this_print",
      text: "What does this print?",
      code: "x = 7\ny = 2\nprint(x / y, x // y, x % y)",
      options: [
        "3.5 3 1",
        "3 3 1",
        "3.5 3.5 1",
        "3.5 3 0",
      ],
      correct_index: 0,
    },
    {
      type: "free",
      subtype: "short_answer",
      text: "In one sentence, why does Python distinguish / from //?",
    },
    {
      type: "free",
      subtype: "stretch_conceptual",
      text: "When would you choose % over // in a sysadmin script, and what would the result represent?",
    },
  ],
};

export const mockExercise: ExerciseResult = {
  exercise: {
    topic: "Arithmetic Operations — converting durations",
    task: "Read a number of seconds from a variable and print the equivalent HH:MM:SS line, zero-padding each segment to two digits. Use only //, %, and an f-string.",
    expected_output: "02:14:09",
    constraints: [
      "No imports; use only arithmetic operators.",
      "Pad each segment to two digits with f-string formatting.",
      "Handle inputs ≥ 24h gracefully (no day rollover).",
    ],
  },
  apply_at_work: {
    angle: "C",
    text: "When logging a Claude API call's latency, store start and end times as time.time() floats and use elapsed_ms = (end - start) * 1000. The // 1000 + % 1000 split lets you log seconds and millis separately for easier eyeballing in the console.",
  },
  angle: "C",
  exercise_text: "**Topic:** Arithmetic Operations — converting durations",
};
