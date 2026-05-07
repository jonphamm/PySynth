# Workflow: Research a Topic

**When to run:** Jon says "run the research workflow on \<topic\>" or "research \<topic\> for me".

**Goal:** Produce one clean, structured markdown report on the requested topic, saved to `Output/research/<topic-slug>.md`, with cited sources.

---

## Steps

### 1. Confirm scope (skip if already obvious)

Before searching, ask 1–2 quick clarifying questions with `AskUserQuestion`:

- **Depth** — quick overview (1-page) vs. deep dive (3+ pages)?
- **Angle** — is there a specific lens (security, cost, beginner-friendly, comparison vs alternative X)?

Skip this step if the topic and scope are unambiguous from how Jon phrased it.

### 2. Gather sources

- Start with `WebSearch` for the topic to map the landscape (3–5 queries varying angles).
- Then use `WebFetch` on the **4–8 most credible/relevant** results.
- **Source priority** (highest to lowest):
  1. Primary sources (official docs, RFCs, vendor announcements, source code)
  2. Peer-reviewed papers, established standards bodies
  3. Reputable technical publications, well-known engineering blogs
  4. Forum/community posts (Stack Overflow, Reddit) — only for sentiment or workarounds, never for facts

Avoid: AI-generated content farms, undated blogs, sites with no clear author or org.

### 3. Take notes (in working memory)

Don't save a separate notes file. Capture in your context:
- Key facts with the source they came from
- Conflicting claims between sources (call these out in the final report)
- Direct quotes worth preserving (use sparingly, attribute clearly)

### 4. Write the report

Save to `Output/research/<topic-slug>.md` where `<topic-slug>` is kebab-case (lowercase, hyphens, no spaces, no punctuation other than hyphens).

**Length target: ~40 lines, ~300 words. Half a page.** Jon skims, he doesn't read.

**Required structure (default):**

```markdown
# <Topic>

*Researched <YYYY-MM-DD>*

## TL;DR

- 3 bullets max — the things Jon needs to decide or act on

## Key Findings

- 5–8 bullets total, ~25 words each
- Cite inline as `[Source N]`
- **No subsections.** If you want to subhead, you're including too much — cut.

## Sources

1. **<Title>** — <URL> (accessed YYYY-MM-DD)
```

**Optional sections** (include only if genuinely material — skip by default):

- `## Background / Why it matters` — only if Jon can't understand the Findings without it. 3 bullets max.
- `## Open Questions / Caveats` — only if there are real unknowns or contested claims that would change Jon's action. 3 bullets max.

If you include either, re-check you're still under 40 lines. If not, cut the optional sections — they earned their way out.

### 5. Style rules (per CLAUDE.md)

- Bullets over paragraphs everywhere except short framing sentences.
- Concise — every bullet earns its place. Cut filler.
- **Stay under 40 lines / ~300 words.** If over, cut findings until under.
- Cite every non-obvious factual claim inline as `[Source N]`. Common knowledge doesn't need a cite.
- No marketing language, no hedging filler ("it's worth noting that…"). Just the claim and the source.

### 6. Confirm

Tell Jon the report path (e.g., `Output/research/prompt-caching-for-anthropic-api.md`) and a 1-sentence summary of what's inside. Don't paste the full report into chat — he can open the file.

---

## Anti-patterns

- Don't fetch 20 sources "to be thorough" — 4–8 quality sources beat 20 mediocre ones.
- Don't synthesize before reading — read all your fetched sources first, then write.
- Don't copy long passages verbatim. Synthesize in your own words; quote only when the exact wording matters.
- Don't make up a date for "accessed" — use today's actual date.
