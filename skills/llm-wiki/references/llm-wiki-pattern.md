# LLM Wiki Pattern

## Suggested Layout

```text
project-root/
  raw/
    sources/
    assets/
  wiki/
    index.md
    log.md
    overview.md
    entities/
    concepts/
    sources/
    analyses/
  CLAUDE.md or AGENTS.md
  purpose.md
```

## Useful Page Types

- Source summary: what a single source says and why it matters
- Entity page: a person, company, project, place, or recurring actor
- Concept page: an idea, theme, framework, or mechanism
- Analysis page: a comparison, thesis update, question answer, or memo worth keeping
- Overview page: the current high-level synthesis of the whole wiki

## Ingest Checklist

1. Read the source and identify the pages it should update.
2. Write or refresh the source summary page first.
3. Update the affected entity and concept pages.
4. Add or refresh cross-links between changed pages.
5. Update `index.md`.
6. Append a timestamped entry to `log.md`.

## Query Checklist

1. Read `index.md` first.
2. Open the smallest set of pages that cover the question.
3. Cite the pages or source summaries that support the answer.
4. If the answer is durable, store it back into `wiki/analyses/`.

## Lint Checklist

- Find pages with no inbound links.
- Find claims that newer sources contradict or supersede.
- Find repeated concepts that deserve their own page.
- Find thin pages that should merge with another page or be expanded.
- Find research gaps that should become new source requests.
