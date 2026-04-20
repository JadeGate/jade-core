---
name: karpathy-guidelines
description: Behavioral guardrails for coding agents. Use when writing, reviewing, refactoring, debugging, or planning code changes so the model surfaces assumptions, prefers the simplest viable approach, avoids unrelated edits, and defines explicit verification criteria before claiming success.
---

# Karpathy Guidelines

Apply four behavior rules that reduce common LLM coding failures on non-trivial engineering work.

## When To Lean On This Skill

- Use for code generation, bug fixes, refactors, reviews, migrations, debugging, and implementation planning.
- Use when the task is ambiguous, spans multiple files, changes an existing codebase, or risks overengineering.
- Keep the same spirit on trivial edits, but skip the full ceremony when the right answer is obvious.

## Operating Loop

### 1. Think before coding

- Reframe the task before editing anything.
- State assumptions explicitly instead of silently picking one interpretation.
- Surface tradeoffs if multiple reasonable implementations exist.
- Stop and resolve confusion before writing code.

### 2. Prefer the smallest viable solution

- Solve only the requested problem.
- Avoid speculative abstractions, configurability, or edge-case scaffolding that the task does not need.
- If the draft feels much larger than the problem, simplify it before moving on.

### 3. Keep the diff surgical

- Match the surrounding style and conventions.
- Touch only files and lines that trace back to the request.
- Remove only the unused code or imports that your own change creates.
- Call out unrelated cleanup opportunities instead of sneaking them into the patch.

### 4. Define a verifiable finish line

- Translate vague requests into checks, tests, or concrete acceptance criteria.
- For bugs, prefer reproduce -> fix -> verify.
- For refactors, preserve behavior and prove it.
- Do not declare success until the relevant verification has run, or the missing verification is called out clearly.

## Planning Pattern

Before implementation, use a compact frame like this whenever the task is not trivial:

```text
Goal:
[one-sentence outcome]

Assumptions:
- ...

Plan:
1. [step] -> verify: [check]
2. [step] -> verify: [check]
```

If assumptions or tradeoffs materially change the solution, resolve them first.

## Review Lens

While reviewing work, actively look for:

- silent assumptions
- overbuilt abstractions
- unrelated file churn
- missing verification
- claims of completion without evidence

## Completion Standard

Treat the task as done only when all of the following are true:

- Every changed line traces back to the request.
- The simplest workable design won.
- Verification exists, or the verification gap is stated explicitly.

## Reference Material

- Read `references/provenance.md` for the upstream source review and packaging notes.
