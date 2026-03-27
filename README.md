# skill-lint

Static analysis and quality scoring for Claude Code SKILL.md files. Like ESLint, but for agent skills.

## What It Checks

### Frontmatter (Structural)
- Required fields present (`name`, `description`)
- Name format: kebab-case, < 64 chars, matches directory name
- Description length: < 1024 chars
- Valid `allowed-tools` entries if present

### Description Quality (Heuristic Scoring)
- Word count analysis (< 15 = too vague, 50-100 = sweet spot)
- Trigger phrase detection ("Use when", "TRIGGER when")
- Anti-trigger phrase detection ("DO NOT TRIGGER when")
- Generic word ratio — flags vague descriptions that undertrigger or overtrigger
- Dual-audience check — readable by humans AND actionable for the AI model

### Body Quality
- Line count (< 500 target)
- Structured sections present (headings)
- Gotchas/pitfalls section (highest-ROI content)
- Progressive disclosure — references used instead of dumping everything in body

### Structure Completeness
- SKILL.md exists
- Referenced scripts/ files are present and executable
- Referenced references/ files exist
- No orphan files (unreferenced scripts or references)
- No broken WikiLinks

## Scoring

```
Skill Score: 72/100

Frontmatter    ██████████  10/10  ✓ All required fields present
Description    ██████░░░░  12/20  ⚠ No anti-trigger phrases
                                   ⚠ 3 generic words without context
Body Structure ████████░░  16/20  ✓ Under 500 lines
                                   ⚠ No gotchas section
References     ██████████  20/20  ✓ All refs resolve
Completeness   ██████░░░░  14/20  ⚠ 2 scripts not referenced in body
                                   ⚠ No evals/ directory
```

## Usage

```bash
# Lint a single skill
python skill_lint.py path/to/skill/

# Lint all skills in a directory
python skill_lint.py path/to/skills/ --all

# Output as JSON (for CI/CD)
python skill_lint.py path/to/skill/ --json

# Strict mode (fail on warnings)
python skill_lint.py path/to/skill/ --strict
```

## Integrations

- **CLI** — run in terminal or CI/CD pipelines
- **Obsidian** — via [skill-viz](https://github.com/patchmyday/skill-viz) plugin (lint on save, score badge per skill)
- **Pre-commit hook** — validate skills before committing

## Companion Tools

- [skill-viz](https://github.com/patchmyday/skill-viz) — Obsidian plugin for browsing, viewing, and creating skills

## Status

Under development.

## License

MIT
