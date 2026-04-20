# Defuddle Notes

## Provenance

- Reviewed source repository: `https://github.com/kepano/defuddle`
- Reviewed commit: `b2a3e5323cb15c53b393e1713cef7813f8bfa1c8`
- Reviewed files:
  - `README.md`
  - `CLAUDE.md`
- License: MIT. The upstream license text is copied to `../LICENSE.txt`.

## Interface Selection

| Interface | Use it for | Entry point |
| --- | --- | --- |
| Browser | Extensions and in-page extraction | `import Defuddle from 'defuddle'` |
| Node.js | Server-side transforms and testing | `import { Defuddle } from 'defuddle/node'` |
| CLI | Quick repros, conversions, and smoke tests | `npx defuddle parse <url-or-file>` |
| Worker | API validation and deployed behavior | `curl http://localhost:8787/...` |

## Useful Options

| Option | Default | Use it when |
| --- | --- | --- |
| `markdown` | `false` | Markdown output is needed |
| `separateMarkdown` | `false` | Both HTML and markdown need to be kept |
| `contentSelector` | unset | Auto-detection picked the wrong root node |
| `debug` | `false` | Removals and selected content need inspection |
| `includeReplies` | `'extractors'` | Forum or thread replies should be included or excluded intentionally |
| `removeLowScoring` | `true` | Non-content scoring needs to be isolated during debugging |
| `standardize` | `true` | Footnote and content normalization need to be bypassed during debugging |

## Debug Checklist

1. Reproduce with the smallest possible page or fixture.
2. Turn on debug mode and inspect `contentSelector` plus `removals`.
3. Disable one pipeline stage at a time.
4. Confirm whether the issue belongs to selector removal, scoring, hidden-element removal, or standardization.
5. Add an anonymized fixture that fails before the fix and passes after the fix.
