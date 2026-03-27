# skill-lint Design Specification

> Static analysis and quality scoring for Claude Code SKILL.md files.
> Like ESLint for JavaScript, but for agent skills.

**Version:** 0.1-draft
**Date:** 2026-03-26
**Status:** Design

---

## Table of Contents

1. [Problem Statement](#1-problem-statement)
2. [Architecture](#2-architecture)
3. [Rule System](#3-rule-system)
4. [Scoring Algorithm](#4-scoring-algorithm)
5. [Description Analysis Deep Dive](#5-description-analysis-deep-dive)
6. [CLI Interface](#6-cli-interface)
7. [Output Format](#7-output-format)
8. [Python API](#8-python-api)
9. [Rule Configuration](#9-rule-configuration)
10. [CI/CD Integration](#10-cicd-integration)
11. [Test Strategy](#11-test-strategy)
12. [Phased Rollout](#12-phased-rollout)
13. [Future: LLM-Enhanced Mode](#13-future-llm-enhanced-mode)

---

## 1. Problem Statement

### Why Static Analysis Matters for Skills

Claude Code skills are an emerging primitive — a markdown-defined unit of agent behavior. As the ecosystem grows (Anthropic's official skill repo, gstack extensions, community skills), there is no automated way to enforce quality. The consequences:

- **Silent activation failures.** A skill with a vague description never triggers when it should, or triggers when it shouldn't. The user never knows the skill exists. There's no error — just absence.
- **Context window waste.** A skill body that dumps 800 lines of instructions inline instead of using progressive disclosure (references/) burns tokens on every activation — tokens the agent could use for reasoning.
- **Broken references.** A skill points to `scripts/deploy.sh` but the file was renamed. The agent hallucinates a workaround or fails silently.
- **No quality floor.** Without a linter, the difference between a polished skill and a broken one is invisible until runtime. There's no CI gate, no pre-commit check, no score to optimize toward.

**skill-lint** solves this by providing deterministic, zero-LLM-cost static analysis that catches these issues before deployment. It gives skill authors a score to optimize and CI pipelines a gate to enforce.

### Design Principles

1. **Zero LLM calls.** All analysis is heuristic-based. Fast, free, deterministic.
2. **Actionable output.** Every diagnostic includes what's wrong, why it matters, and how to fix it.
3. **Gradual adoption.** Works out of the box with zero config. Strictness is opt-in.
4. **Composable.** CLI for humans, JSON/SARIF for CI, Python API for tools like skill-viz.

---

## 2. Architecture

### Package Structure

```
skill-lint/
├── docs/
│   └── design.md              # This document
├── src/
│   └── skill_lint/
│       ├── __init__.py         # Public API: lint(), score(), LintResult
│       ├── __main__.py         # `python -m skill_lint` entry point
│       ├── cli.py              # argparse CLI, terminal output formatting
│       ├── parser.py           # SKILL.md parsing: frontmatter + body extraction
│       ├── scorer.py           # Scoring algorithm: rules → points → grade
│       ├── rules/
│       │   ├── __init__.py     # Rule registry, rule discovery
│       │   ├── base.py         # BaseRule ABC, Severity enum, RuleDiagnostic
│       │   ├── frontmatter.py  # FM-* rules
│       │   ├── description.py  # DESC-* rules
│       │   ├── body.py         # BODY-* rules
│       │   ├── references.py   # REF-* rules
│       │   └── completeness.py # COMP-* rules
│       ├── config.py           # .skilllintrc loading and merging
│       ├── formatters/
│       │   ├── __init__.py
│       │   ├── terminal.py     # Colored terminal output with score bars
│       │   ├── json.py         # JSON output for programmatic use
│       │   └── sarif.py        # SARIF output for GitHub Code Scanning
│       └── wordlists.py        # Trigger phrases, anti-trigger phrases, generic words
├── tests/
│   ├── conftest.py
│   ├── test_parser.py
│   ├── test_scorer.py
│   ├── test_rules/
│   │   ├── test_frontmatter.py
│   │   ├── test_description.py
│   │   ├── test_body.py
│   │   ├── test_references.py
│   │   └── test_completeness.py
│   ├── test_cli.py
│   ├── test_config.py
│   └── fixtures/               # Test skills with known scores
│       ├── perfect_skill/
│       ├── minimal_skill/
│       ├── broken_skill/
│       └── ...
├── pyproject.toml
├── .skilllintrc.default        # Default configuration
└── README.md
```

### Data Flow

```
Skill Directory
      │
      ▼
   parser.py ──────► SkillData (frontmatter, body, files, structure)
      │
      ▼
   rules/*.py ─────► List[RuleDiagnostic] (rule ID, severity, message, fix)
      │
      ▼
   scorer.py ──────► ScoreResult (per-category scores, total, grade)
      │
      ▼
   formatters/*.py ► Output (terminal / JSON / SARIF)
```

### Core Data Models

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

class Severity(Enum):
    ERROR = "error"      # Must fix. Indicates broken functionality.
    WARNING = "warning"  # Should fix. Reduces quality or reliability.
    INFO = "info"        # Nice to have. Best practice suggestion.

class Category(Enum):
    FRONTMATTER = "frontmatter"
    DESCRIPTION = "description"
    BODY = "body"
    REFERENCES = "references"
    COMPLETENESS = "completeness"
    BONUS = "bonus"

@dataclass
class RuleDiagnostic:
    rule_id: str            # e.g., "FM-001"
    category: Category
    severity: Severity
    message: str            # What's wrong
    reason: str             # Why it matters
    fix: str | None         # How to fix it (None if obvious)
    line: int | None        # Line number in SKILL.md (None for structural issues)
    score_impact: float     # Points deducted (negative) or awarded (positive)

@dataclass
class SkillData:
    path: Path
    frontmatter: dict           # Parsed YAML frontmatter
    body: str                   # Markdown body after frontmatter
    body_lines: list[str]
    files: dict[str, list[Path]]  # {"scripts": [...], "references": [...], ...}
    raw_content: str

@dataclass
class CategoryScore:
    category: Category
    earned: float
    possible: float
    diagnostics: list[RuleDiagnostic]

@dataclass
class ScoreResult:
    total: float              # 0-100
    grade: str                # A+, A, B, C, D, F
    categories: list[CategoryScore]
    diagnostics: list[RuleDiagnostic]
    skill_path: Path
```

---

## 3. Rule System

Every rule has:
- **ID**: `{CATEGORY_PREFIX}-{NNN}` — stable across versions
- **Category**: Which scoring bucket it belongs to
- **Severity**: error / warning / info
- **Default**: enabled / disabled
- **Score weight**: Points deducted or awarded
- **What**: What it checks
- **Why**: Why it matters
- **Fix**: Suggested remediation

### 3.1 Frontmatter Rules (FM-*) — 10 points possible

| ID | Name | Severity | Weight | What | Why |
|----|------|----------|--------|------|-----|
| FM-001 | `missing-skill-md` | error | -10 | SKILL.md file exists in directory | No SKILL.md = not a skill. Fatal. |
| FM-002 | `missing-frontmatter` | error | -10 | YAML frontmatter block exists (`---` delimiters) | Frontmatter is required for skill metadata. Without it, nothing works. |
| FM-003 | `missing-name` | error | -5 | `name` field exists in frontmatter | Name is required by the spec. |
| FM-004 | `name-format` | warning | -2 | `name` is kebab-case and < 64 chars | Spec requires kebab-case. Non-conforming names may not resolve. |
| FM-005 | `missing-description` | error | -5 | `description` field exists in frontmatter | Description is THE trigger mechanism. Without it, the skill never activates. |
| FM-006 | `description-length` | warning | -2 | `description` is ≤ 1024 characters | Spec hard limit. Longer descriptions are truncated. |
| FM-007 | `invalid-yaml` | error | -10 | Frontmatter parses as valid YAML | Broken YAML = broken skill. |
| FM-008 | `unknown-fields` | info | 0 | Warn on frontmatter fields not in the spec | May indicate typos (e.g., `descrption`). |

**Scoring:** Start at 10. Each rule deducts its weight. Floor at 0. Cap at 10.

### 3.2 Description Quality Rules (DESC-*) — 20 points possible

| ID | Name | Severity | Weight | What | Why |
|----|------|----------|--------|------|-----|
| DESC-001 | `description-too-short` | warning | -5 | Description < 30 words | Too short to convey purpose. AI can't reliably trigger. |
| DESC-002 | `description-too-long` | warning | -3 | Description > 150 words | Wastes preamble tokens. Should be concise. |
| DESC-003 | `description-sweet-spot` | info | +3 | Description is 50–100 words | Optimal range per research. Bonus for hitting it. |
| DESC-004 | `missing-trigger-phrase` | warning | -5 | No trigger phrases found (see §5.2) | Trigger phrases tell the AI *when* to activate. Without them, activation is unreliable. |
| DESC-005 | `has-trigger-phrase` | info | +3 | At least one trigger phrase present | Positive signal. |
| DESC-006 | `missing-anti-trigger` | info | -2 | No anti-trigger phrases found (see §5.3) | Anti-triggers prevent false positives. Important for precision. |
| DESC-007 | `has-anti-trigger` | info | +2 | At least one anti-trigger phrase present | Positive signal. |
| DESC-008 | `high-generic-ratio` | warning | -4 | > 30% of words are generic (see §5.4) | Generic descriptions match everything and nothing. |
| DESC-009 | `low-generic-ratio` | info | +2 | < 15% of words are generic | Specific descriptions trigger accurately. |
| DESC-010 | `no-dual-audience` | warning | -3 | Description lacks both human-readable AND AI-actionable phrasing | Must serve both audiences. See §5.5. |
| DESC-011 | `has-dual-audience` | info | +2 | Description has both human and AI phrasing | Positive signal. |
| DESC-012 | `description-starts-generic` | warning | -2 | First sentence is generic (e.g., "A skill that helps with...") | First sentence is most visible in listings. Should be specific. |

**Scoring:** Start at 8 base points (for having a description at all). Add bonuses, subtract penalties. Floor at 0. Cap at 20.

### 3.3 Body Structure Rules (BODY-*) — 20 points possible

| ID | Name | Severity | Weight | What | Why |
|----|------|----------|--------|------|-----|
| BODY-001 | `body-too-long` | warning | -5 | Body > 500 lines | Long bodies waste context tokens on every activation. Use references/. |
| BODY-002 | `body-very-long` | error | -10 | Body > 1000 lines | Severely impacts performance. Almost certainly should use progressive disclosure. |
| BODY-003 | `no-headings` | warning | -4 | Body has zero markdown headings (`#`, `##`, etc.) | Headings provide structure for both humans and AI parsing. |
| BODY-004 | `few-headings` | info | -2 | Body > 50 lines but < 3 headings | Long bodies need more structure. |
| BODY-005 | `no-gotchas-section` | warning | -3 | No "Gotchas", "Caveats", "Pitfalls", "Common Mistakes", or "Known Issues" heading | Gotchas sections have highest ROI — they prevent the most common failures. |
| BODY-006 | `has-gotchas-section` | info | +3 | Gotchas/caveats section present | Positive signal. |
| BODY-007 | `no-examples` | info | -2 | No code blocks or example sections | Examples help the AI understand expected behavior. |
| BODY-008 | `inline-dump` | warning | -3 | Body contains > 200 lines without referencing external files | Likely dumping content inline instead of using references/. |
| BODY-009 | `empty-body` | warning | -5 | Body is empty or < 10 lines | Skill has no instructions. Frontmatter alone is rarely sufficient. |
| BODY-010 | `has-progressive-disclosure` | info | +2 | Body references files in `references/` directory | Uses progressive disclosure correctly. |

**Scoring:** Start at 10 base points. Add bonuses, subtract penalties. Floor at 0. Cap at 20.

### 3.4 Reference Rules (REF-*) — 20 points possible

| ID | Name | Severity | Weight | What | Why |
|----|------|----------|--------|------|-----|
| REF-001 | `broken-file-reference` | error | -4 each | Body mentions a file path that doesn't exist in the skill directory | Agent will fail trying to read a nonexistent file. |
| REF-002 | `script-not-executable` | error | -3 each | File in `scripts/` lacks execute permission | Agent can't run non-executable scripts. |
| REF-003 | `broken-relative-link` | warning | -2 each | Markdown link `[text](path)` points to nonexistent file | Broken links frustrate both humans and AI. |
| REF-004 | `unreferenced-script` | warning | -2 each | File in `scripts/` not mentioned anywhere in SKILL.md | Orphan script — either dead code or missing documentation. |
| REF-005 | `unreferenced-reference` | info | -1 each | File in `references/` not mentioned in SKILL.md body | Reference exists but skill never tells agent to read it. |
| REF-006 | `empty-directory` | info | -1 each | A standard directory (`scripts/`, `references/`, `agents/`, `assets/`, `evals/`) exists but is empty | Empty dirs suggest incomplete implementation. |
| REF-007 | `all-refs-resolve` | info | +5 | Every file reference in body resolves to an existing file | All references are valid. Positive signal. |
| REF-008 | `all-scripts-executable` | info | +3 | Every script in `scripts/` is executable | Clean execution environment. |
| REF-009 | `script-has-shebang` | warning | -1 each | Script lacks a shebang line (`#!/...`) | Without a shebang, the agent may invoke with the wrong interpreter. |

**Scoring:** Start at 5 base points (for having a skill directory). Add bonuses, subtract penalties based on actual files found. Floor at 0. Cap at 20. If no references/scripts exist and skill is under 100 lines, no penalty (simple skills don't need them).

### 3.5 Completeness Rules (COMP-*) — 20 points possible

| ID | Name | Severity | Weight | What | Why |
|----|------|----------|--------|------|-----|
| COMP-001 | `has-scripts-dir` | info | +2 | `scripts/` directory exists with files | Skill has executable tooling. |
| COMP-002 | `has-references-dir` | info | +2 | `references/` directory exists with files | Skill uses progressive disclosure. |
| COMP-003 | `has-agents-dir` | info | +2 | `agents/` directory exists with files | Skill supports multi-agent orchestration. |
| COMP-004 | `has-evals-dir` | info | +3 | `evals/` directory exists with files | Skill is testable. High quality signal. |
| COMP-005 | `has-assets-dir` | info | +1 | `assets/` directory exists with files | Skill packages its assets. |
| COMP-006 | `scripts-documented` | info | +3 | Every file in `scripts/` is mentioned in SKILL.md body | Full documentation of tooling. |
| COMP-007 | `no-orphan-files` | info | +2 | No files outside standard directories (except SKILL.md, README, LICENSE, config files) | Clean structure, no loose files. |
| COMP-008 | `has-readme` | info | +1 | README.md exists | Human-readable docs beyond the skill itself. |
| COMP-009 | `structure-complete` | info | +4 | Has at least 3 of: scripts/, references/, agents/, evals/, assets/ | Well-structured skill with supporting infrastructure. |

**Scoring:** Start at 0. Add points for each completeness signal. Floor at 0. Cap at 20.

### 3.6 Bonus Rules (BONUS-*) — 10 points possible

These check for gstack extensions and best practices beyond the core spec.

| ID | Name | Severity | Weight | What | Why |
|----|------|----------|--------|------|-----|
| BONUS-001 | `has-version` | info | +2 | `version` field in frontmatter (valid semver) | Enables dependency management and changelog tracking. |
| BONUS-002 | `has-benefits-from` | info | +2 | `benefits-from` field declares dependencies | Explicit dependency chain for skill composition. |
| BONUS-003 | `has-allowed-tools` | info | +2 | `allowed-tools` field specifies tool requirements | Declares what the skill needs — helps both the runtime and humans understand scope. |
| BONUS-004 | `has-license` | info | +1 | `license` field present | Important for distribution and legal clarity. |
| BONUS-005 | `has-compatibility` | info | +1 | `compatibility` field present | Declares which Claude Code versions the skill supports. |
| BONUS-006 | `has-preamble-tier` | info | +2 | `preamble-tier` field with value 1–4 | gstack extension for context loading priority. |

**Scoring:** Start at 0. Add points for each bonus. Cap at 10.

---

## 4. Scoring Algorithm

### Point Calculation

```python
def calculate_score(diagnostics: list[RuleDiagnostic]) -> ScoreResult:
    # Group diagnostics by category
    by_category = group_by(diagnostics, key=lambda d: d.category)

    category_scores = []
    for category in Category:
        config = CATEGORY_CONFIG[category]
        base = config.base_points
        earned = base

        for diag in by_category.get(category, []):
            earned += diag.score_impact  # Negative for penalties, positive for bonuses

        earned = max(0, min(config.max_points, earned))
        category_scores.append(CategoryScore(category, earned, config.max_points, ...))

    total = sum(cs.earned for cs in category_scores)
    grade = points_to_grade(total)

    return ScoreResult(total, grade, category_scores, diagnostics)
```

### Category Configuration

| Category | Base Points | Max Points |
|----------|-------------|------------|
| Frontmatter | 10 | 10 |
| Description | 8 | 20 |
| Body | 10 | 20 |
| References | 5 | 20 |
| Completeness | 0 | 20 |
| Bonus | 0 | 10 |
| **Total** | — | **100** |

### Grade Thresholds

| Grade | Score Range | Meaning |
|-------|-------------|---------|
| A+ | 95–100 | Exemplary. Best-in-class skill. |
| A | 85–94 | Excellent. Production-ready, well-structured. |
| B | 70–84 | Good. Works well, minor improvements possible. |
| C | 55–69 | Acceptable. Functional but has notable gaps. |
| D | 40–54 | Poor. Works but has significant quality issues. |
| F | 0–39 | Failing. Likely broken or severely incomplete. |

### Fatal Rule Handling

If any **error**-severity rule in the Frontmatter category fires (FM-001, FM-002, FM-007), the skill is immediately graded **F** regardless of other scores, because the skill cannot function at all.

---

## 5. Description Analysis Deep Dive

The description is the most important field in a skill. It's the trigger mechanism — the text that the Claude Code harness matches against user prompts to decide whether to activate a skill. Getting it right is the difference between a skill that works and one that sits dormant.

### 5.1 Word Count Scoring

```
Words     Score Effect     Reasoning
──────    ────────────     ─────────
< 10      -5 (error)      Effectively empty. Cannot convey purpose.
10-29     -5 (warning)    Too short. Triggers unreliably.
30-49     0               Adequate but not optimal.
50-100    +3 (bonus)      Sweet spot. Enough detail without bloat.
101-150   0               Acceptable but wordy.
> 150     -3 (warning)    Too long. Wastes preamble tokens.
```

### 5.2 Trigger Phrase Detection

Trigger phrases tell the AI *when* to activate the skill. The linter searches for these patterns (case-insensitive):

**Primary triggers** (strong signal):
- `"TRIGGER when"`
- `"Use when"`
- `"Use this when"`
- `"Use this skill when"`
- `"Activate when"`
- `"Run when"`
- `"Invoke when"`

**Secondary triggers** (moderate signal):
- `"Use for"`
- `"Use this for"`
- `"Helpful for"`
- `"Designed for"`
- `"Best for"`
- `"Good for"`
- `"Examples:"`
- `"e.g.,"`
- `"such as"`

**Scoring:**
- 0 trigger phrases found → -5 points (DESC-004)
- ≥ 1 primary trigger → +3 points (DESC-005)
- ≥ 1 secondary trigger only → +1 point (partial DESC-005)

### 5.3 Anti-Trigger Phrase Detection

Anti-triggers prevent false positives — they tell the AI when *not* to activate.

**Anti-trigger patterns** (case-insensitive):
- `"DO NOT TRIGGER when"`
- `"DO NOT use when"`
- `"Do not use for"`
- `"NOT for"`
- `"Don't use when"`
- `"Don't trigger when"`
- `"Avoid using when"`
- `"Not intended for"`
- `"Do NOT use this for"`
- `"Should not be used for"`
- `"Except when"`
- `"Unless"`

**Scoring:**
- 0 anti-triggers found → -2 points (DESC-006)
- ≥ 1 anti-trigger found → +2 points (DESC-007)

### 5.4 Generic Word Detection

Generic words reduce description specificity. A description full of generic words matches everything and triggers on the wrong prompts.

**Generic word list:**
```python
GENERIC_WORDS = {
    "help", "helps", "helpful", "assist", "assists", "assistance",
    "tool", "tools", "utility", "utilities",
    "manage", "manages", "management", "handle", "handles", "handling",
    "process", "processes", "processing",
    "work", "works", "working",
    "thing", "things", "stuff",
    "good", "great", "nice", "better", "best",
    "simple", "simply", "easy", "easily",
    "various", "multiple", "different", "several",
    "general", "generally", "generic",
    "support", "supports", "supporting",
    "provide", "provides", "providing",
    "enable", "enables", "enabling",
    "allow", "allows", "allowing",
    "perform", "performs", "performing",
    "create", "creates", "creating",  # only generic when not followed by specific noun
    "basic", "advanced",
    "important", "useful", "relevant",
}
```

**Ratio calculation:**
```python
def generic_ratio(description: str) -> float:
    words = tokenize(description)  # lowercase, strip punctuation
    content_words = [w for w in words if w not in STOP_WORDS]
    if not content_words:
        return 1.0
    generic_count = sum(1 for w in content_words if w in GENERIC_WORDS)
    return generic_count / len(content_words)
```

**Scoring:**
- Ratio > 0.30 → -4 points (DESC-008)
- Ratio 0.15–0.30 → 0 points (neutral)
- Ratio < 0.15 → +2 points (DESC-009)

### 5.5 Dual-Audience Check

The description must serve two audiences: humans (who read it in listings/docs) and AI (who uses it for activation matching). The linter checks for both signals:

**Human-readable signals:**
- Contains a plain-English sentence (not just keywords)
- First sentence could appear in a directory listing
- Has at least one sentence that doesn't start with a directive keyword

**AI-actionable signals:**
- Contains trigger phrase (from §5.2)
- Contains anti-trigger phrase (from §5.3)
- Contains specific technical terms, file extensions, or tool names
- Contains structured markers: "TRIGGER", "Use when", "Examples:"

**Scoring:**
- Has both human + AI signals → +2 points (DESC-011)
- Has only one → 0 points
- Has neither → -3 points (DESC-010)

### 5.6 First-Sentence Analysis

```python
GENERIC_OPENERS = [
    r"^a (tool|skill|utility) (that|which|for)",
    r"^this (tool|skill|utility) (helps|assists|provides|enables)",
    r"^(helps|assists) (you |users )?(to )?(with|in|by)",
    r"^(use|useful) for",
    r"^a? ?general[- ]purpose",
]
```

If the first sentence matches any generic opener → -2 points (DESC-012).

---

## 6. CLI Interface

### Command Syntax

```
skill-lint [OPTIONS] [PATH...]
```

### Positional Arguments

| Argument | Description |
|----------|-------------|
| `PATH` | One or more paths to skill directories. If omitted, uses current directory. |

### Options

| Flag | Short | Description |
|------|-------|-------------|
| `--all` | `-a` | Lint all subdirectories that contain SKILL.md |
| `--json` | `-j` | Output JSON instead of terminal format |
| `--sarif` | | Output SARIF format for GitHub Code Scanning |
| `--strict` | `-s` | Exit code 1 if any warnings (default: only errors cause exit 1) |
| `--min-score N` | | Exit code 1 if total score < N (e.g., `--min-score 70`) |
| `--fix` | `-f` | Auto-fix what can be fixed (e.g., add execute permissions to scripts) |
| `--config PATH` | `-c` | Path to .skilllintrc config file |
| `--no-color` | | Disable colored output |
| `--quiet` | `-q` | Only show score and grade (suppress diagnostics) |
| `--verbose` | `-v` | Show all rules including passing ones |
| `--version` | `-V` | Print version and exit |
| `--list-rules` | | Print all rules with IDs, descriptions, and default severity |
| `--rule RULE_ID` | | Only run specified rules (can be repeated) |
| `--disable RULE_ID` | | Disable specified rules (can be repeated) |
| `--category CAT` | | Only run rules in specified category |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success. No errors found (warnings may exist unless `--strict`). |
| 1 | Lint failure. Errors found, or `--strict` with warnings, or `--min-score` not met. |
| 2 | Usage error. Invalid arguments. |

### Examples

```bash
# Lint current directory
skill-lint .

# Lint a specific skill
skill-lint path/to/my-skill/

# Lint all skills in a directory
skill-lint --all skills/

# CI mode: fail if score < 70
skill-lint --min-score 70 --json path/to/skill/

# Strict mode
skill-lint --strict path/to/skill/

# Auto-fix
skill-lint --fix path/to/skill/

# List all rules
skill-lint --list-rules
```

---

## 7. Output Format

### Terminal Output (Default)

```
  skill-lint v0.1.0

  📂 my-awesome-skill/

  ── Frontmatter ──────────────────────────── 10 / 10
     ✓ All required fields present
     ✓ Name format valid (kebab-case, 22 chars)

  ── Description ──────────────────────────── 17 / 20
     ✓ Word count: 72 (sweet spot)
     ✓ Trigger phrase: "Use when"
     ✓ Anti-trigger: "DO NOT TRIGGER when"
     ⚠ DESC-008  Generic word ratio: 22% (threshold: < 15% for bonus)
                  ↳ Try replacing generic words: "help", "manage", "process"

  ── Body Structure ───────────────────────── 18 / 20
     ✓ Line count: 187 (under 500)
     ✓ 6 headings found
     ✓ Gotchas section present
     ⚠ BODY-007  No code examples found
                  ↳ Add a code block showing expected usage

  ── References ───────────────────────────── 20 / 20
     ✓ All file references resolve (4 files)
     ✓ All scripts executable (2 scripts)

  ── Completeness ─────────────────────────── 12 / 20
     ✓ scripts/ (2 files)
     ✓ references/ (2 files)
     ✗ No evals/ directory
     ✗ No agents/ directory

  ── Bonus ────────────────────────────────── 5 / 10
     ✓ version: 1.2.0
     ✓ allowed-tools declared
     ✗ No benefits-from field
     ✗ No license field
     ✗ No preamble-tier field

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Score: 82 / 100                    Grade: B
  ████████████████████░░░░░           82%
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  2 warnings, 0 errors
```

### Color Scheme

- Score bar: green (≥85), yellow (55-84), red (<55)
- `✓` items: green
- `⚠` items: yellow
- `✗` items: dim/gray
- `✗` errors: red
- Rule IDs: cyan
- Fix suggestions (`↳`): dim white

### Batch Output (--all)

```
  skill-lint v0.1.0 — 12 skills found

  Score  Grade  Skill
  ─────  ─────  ─────
   95    A+     pdf
   91    A      pptx
   82    B      docx
   78    B      slack-gif-creator
   67    C      web-artifacts-builder
   52    D      my-broken-skill
   23    F      empty-skill

  ─────────────────────────────────────────
  Average: 69.7    Median: 78    Range: 23–95
  3 passing (≥70)  2 warnings (55-69)  2 failing (<55)
```

### JSON Output (--json)

```json
{
  "version": "0.1.0",
  "skill_path": "my-awesome-skill/",
  "score": {
    "total": 82,
    "grade": "B",
    "categories": {
      "frontmatter": {"earned": 10, "possible": 10},
      "description": {"earned": 17, "possible": 20},
      "body": {"earned": 18, "possible": 20},
      "references": {"earned": 20, "possible": 20},
      "completeness": {"earned": 12, "possible": 20},
      "bonus": {"earned": 5, "possible": 10}
    }
  },
  "diagnostics": [
    {
      "rule_id": "DESC-008",
      "category": "description",
      "severity": "warning",
      "message": "Generic word ratio: 22% (threshold: < 15% for bonus)",
      "fix": "Try replacing generic words: \"help\", \"manage\", \"process\"",
      "line": null,
      "score_impact": -4
    }
  ],
  "summary": {
    "errors": 0,
    "warnings": 2,
    "info": 8
  }
}
```

### SARIF Output (--sarif)

Standard SARIF 2.1.0 for GitHub Code Scanning integration. Each diagnostic maps to a SARIF `result` with:
- `ruleId`: skill-lint rule ID
- `level`: error → error, warning → warning, info → note
- `message.text`: Diagnostic message
- `locations[0].physicalLocation`: Path to SKILL.md + line number

---

## 8. Python API

### Public Interface

```python
from skill_lint import lint, score, LintResult

# Lint a single skill
result: LintResult = lint("path/to/skill/")
print(result.score.total)       # 82
print(result.score.grade)       # "B"
print(result.diagnostics)       # List[RuleDiagnostic]

# Score only (no diagnostics detail)
score_result = score("path/to/skill/")
print(score_result.total)       # 82

# Lint with custom config
result = lint("path/to/skill/", config={"rules": {"BODY-007": "off"}})

# Lint multiple skills
from skill_lint import lint_batch

results = lint_batch("skills/", pattern="*/")
for r in results:
    print(f"{r.skill_path}: {r.score.grade}")

# Access parsed skill data
print(result.skill_data.frontmatter["name"])
print(result.skill_data.body_lines[:5])
```

### LintResult Dataclass

```python
@dataclass
class LintResult:
    skill_data: SkillData
    score: ScoreResult
    diagnostics: list[RuleDiagnostic]
    config: dict

    @property
    def passed(self) -> bool:
        """True if no error-severity diagnostics."""
        return not any(d.severity == Severity.ERROR for d in self.diagnostics)

    @property
    def errors(self) -> list[RuleDiagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.ERROR]

    @property
    def warnings(self) -> list[RuleDiagnostic]:
        return [d for d in self.diagnostics if d.severity == Severity.WARNING]

    def to_json(self) -> dict:
        """Serialize to JSON-compatible dict."""
        ...

    def to_sarif(self) -> dict:
        """Serialize to SARIF 2.1.0 format."""
        ...
```

### Integration Example: skill-viz

```python
# skill-viz Obsidian plugin integration
from skill_lint import lint_batch

def generate_skill_scores(skills_dir: str) -> dict:
    """Generate score data for Obsidian visualization."""
    results = lint_batch(skills_dir)
    return {
        r.skill_data.frontmatter.get("name", r.skill_data.path.name): {
            "score": r.score.total,
            "grade": r.score.grade,
            "categories": {
                cs.category.value: cs.earned
                for cs in r.score.categories
            },
        }
        for r in results
    }
```

---

## 9. Rule Configuration

### Config File: `.skilllintrc`

YAML format. Searched in order:
1. Path passed via `--config`
2. `.skilllintrc` in the skill directory being linted
3. `.skilllintrc` in the current working directory
4. `~/.config/skill-lint/.skilllintrc` (user global)
5. Built-in defaults

Files are merged: more specific configs override less specific ones.

### Config Schema

```yaml
# .skilllintrc

# Override rule severity or disable rules
rules:
  DESC-006: "off"           # Disable this rule entirely
  BODY-007: "error"         # Upgrade from info to error
  COMP-004: "off"           # Don't require evals/

# Adjust scoring weights
scoring:
  categories:
    frontmatter: 10          # Max points (default: 10)
    description: 20          # Default: 20
    body: 20                 # Default: 20
    references: 20           # Default: 20
    completeness: 20         # Default: 20
    bonus: 10                # Default: 10

  grades:
    A+: 95
    A: 85
    B: 70
    C: 55
    D: 40
    # Below D threshold = F

# Adjust thresholds
thresholds:
  description_word_count:
    min: 30                  # Below this = too short
    sweet_min: 50            # Sweet spot lower bound
    sweet_max: 100           # Sweet spot upper bound
    max: 150                 # Above this = too long
  body_line_count:
    warn: 500                # Warning threshold
    error: 1000              # Error threshold
  generic_ratio:
    good: 0.15               # Below = bonus
    bad: 0.30                # Above = penalty

# Custom word lists (merged with defaults)
wordlists:
  generic_words_add:         # Add to the built-in generic word list
    - "leverage"
    - "utilize"
  generic_words_remove:      # Remove from the built-in list
    - "create"               # "create" is meaningful in your domain
  trigger_phrases_add:
    - "Activate for"

# Auto-fix settings
fix:
  add_execute_permission: true
  # Future: add_shebang, normalize_name, etc.
```

### Inline Rule Suppression

Within SKILL.md, suppress specific rules with HTML comments:

```markdown
<!-- skill-lint-disable DESC-008 -->
A general-purpose helper tool that manages various processes.
<!-- skill-lint-enable DESC-008 -->
```

Or disable for the whole file:

```markdown
<!-- skill-lint-disable-file BODY-001 -->
```

---

## 10. CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/skill-lint.yml
name: Skill Lint

on:
  pull_request:
    paths:
      - 'skills/**'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install skill-lint
        run: pip install skill-lint

      - name: Lint all skills
        run: skill-lint --all --min-score 70 --json skills/ > lint-results.json

      - name: Upload SARIF
        if: always()
        run: |
          skill-lint --all --sarif skills/ > results.sarif
          # Upload to GitHub Code Scanning
          gh api \
            -X POST \
            -H "Accept: application/vnd.github+json" \
            /repos/${{ github.repository }}/code-scanning/sarifs \
            -f "commit_sha=${{ github.sha }}" \
            -f "ref=${{ github.ref }}" \
            -f "sarif=$(gzip -c results.sarif | base64 -w0)"

      - name: Comment PR with scores
        if: github.event_name == 'pull_request'
        run: |
          python -c "
          import json
          results = json.load(open('lint-results.json'))
          # Generate markdown table from results
          " | gh pr comment ${{ github.event.number }} --body-file -
```

### Pre-commit Hook

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/your-org/skill-lint
    rev: v0.1.0
    hooks:
      - id: skill-lint
        name: Lint SKILL.md files
        entry: skill-lint --strict
        files: 'SKILL\.md$'
        types: [markdown]
```

### Standalone Pre-commit Script

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit (or scripts/pre-commit.sh)

# Find changed skill directories
changed_skills=$(git diff --cached --name-only | grep 'SKILL\.md' | xargs -I{} dirname {})

if [ -n "$changed_skills" ]; then
    echo "Running skill-lint on changed skills..."
    for skill in $changed_skills; do
        skill-lint --strict "$skill" || exit 1
    done
fi
```

---

## 11. Test Strategy

### Test Pyramid

```
                  ┌─────────────┐
                  │  E2E (CLI)  │  5 tests — full CLI invocations
                  ├─────────────┤
                 │  Integration  │  15 tests — parser + rules + scorer
                ├───────────────┤
               │   Unit Tests    │  80+ tests — individual rules, scorer math
              └──────────────────┘
```

### Test Fixtures

Create skill directories with known expected scores:

| Fixture | Expected Score | Expected Grade | Purpose |
|---------|---------------|----------------|---------|
| `perfect_skill/` | 95-100 | A+ | All rules pass, all bonuses earned |
| `good_skill/` | 80-89 | B+ | Typical well-made skill |
| `minimal_skill/` | 45-55 | D | Only required fields, nothing else |
| `broken_frontmatter/` | 0 | F | Invalid YAML in frontmatter |
| `missing_skill_md/` | 0 | F | No SKILL.md file |
| `long_body/` | 50-65 | C | 800-line body, no references |
| `vague_description/` | 40-55 | D | Generic description, no triggers |
| `broken_refs/` | 30-50 | D-F | References to nonexistent files |
| `gstack_extended/` | 90-100 | A | Has all gstack bonus fields |

### Test Categories

**Unit tests (per rule):**
```python
def test_fm003_missing_name():
    skill = make_skill(frontmatter={"description": "test"})
    diags = FrontmatterRules().run(skill)
    assert any(d.rule_id == "FM-003" for d in diags)

def test_fm003_name_present():
    skill = make_skill(frontmatter={"name": "my-skill", "description": "test"})
    diags = FrontmatterRules().run(skill)
    assert not any(d.rule_id == "FM-003" for d in diags)
```

**Scorer tests:**
```python
def test_grade_boundaries():
    assert points_to_grade(95) == "A+"
    assert points_to_grade(94) == "A"
    assert points_to_grade(85) == "A"
    assert points_to_grade(84) == "B"
    assert points_to_grade(70) == "B"
    assert points_to_grade(69) == "C"
    # ...

def test_category_floor_at_zero():
    """Category score never goes negative."""
    diags = [RuleDiagnostic(score_impact=-50, ...)]
    score = calculate_category(Category.DESCRIPTION, diags)
    assert score.earned == 0
```

**Description analysis tests:**
```python
def test_trigger_phrase_detection():
    desc = "Use when the user asks about PDF files."
    phrases = detect_trigger_phrases(desc)
    assert "Use when" in phrases

def test_generic_ratio_high():
    desc = "A helpful tool that manages various processes and handles different things."
    ratio = generic_ratio(desc)
    assert ratio > 0.30

def test_generic_ratio_low():
    desc = "Convert PDF files to searchable text using OCR with Tesseract."
    ratio = generic_ratio(desc)
    assert ratio < 0.15
```

**Integration tests:**
```python
def test_perfect_skill_scores_a_plus(fixtures_dir):
    result = lint(fixtures_dir / "perfect_skill")
    assert result.score.grade == "A+"
    assert result.score.total >= 95

def test_broken_frontmatter_scores_f(fixtures_dir):
    result = lint(fixtures_dir / "broken_frontmatter")
    assert result.score.grade == "F"
```

**CLI tests:**
```python
def test_cli_json_output(tmp_path):
    result = subprocess.run(
        ["skill-lint", "--json", str(tmp_path / "skill")],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    assert "score" in data
    assert "diagnostics" in data

def test_cli_min_score_exit_code(tmp_path):
    result = subprocess.run(
        ["skill-lint", "--min-score", "90", str(tmp_path / "minimal_skill")],
        capture_output=True
    )
    assert result.returncode == 1
```

---

## 12. Phased Rollout

### v0.1 — Core Rules + CLI (Week 1-2)

**Scope:**
- Parser: SKILL.md frontmatter + body extraction
- Rules: FM-001 through FM-007, DESC-001 through DESC-005, BODY-001, BODY-003, BODY-009
- Scorer: Basic point calculation, grade assignment
- CLI: Terminal output (colored), `--json` flag
- Test fixtures: 3 basic fixtures

**Deliverable:** `python skill_lint.py path/to/skill/` works with terminal output and JSON.

### v0.2 — Full Rule Set (Week 3-4)

**Scope:**
- All remaining rules across all categories
- Description deep analysis (generic ratio, dual-audience check)
- Reference validation (file existence, execute permissions, shebang checks)
- Completeness scoring
- Bonus rules (gstack extensions)
- `--all` batch mode
- `--strict` and `--min-score` flags

### v0.3 — Configuration + CI (Week 5-6)

**Scope:**
- `.skilllintrc` configuration file loading and merging
- Inline rule suppression (`<!-- skill-lint-disable -->`)
- `--sarif` output format
- GitHub Actions workflow template
- Pre-commit hook support
- `--fix` for auto-fixable issues (execute permissions, etc.)
- `--list-rules` and `--disable` flags

### v0.4 — Python API + Integration (Week 7-8)

**Scope:**
- Clean public Python API (`from skill_lint import lint, score`)
- PyPI package (`pip install skill-lint`)
- skill-viz integration adapter
- Comprehensive test suite (80+ tests, all fixtures)
- Documentation: README, contributing guide

### v1.0 — Stable Release (Week 9-10)

**Scope:**
- API stability guarantee
- Performance optimization for large skill directories (100+ skills)
- Full SARIF integration with GitHub Code Scanning
- Aggregate reporting (averages, trends across batches)
- `skill-lint init` command to scaffold a new skill directory

---

## 13. Future: LLM-Enhanced Mode

### Design Philosophy

The core linter is and will always be **zero-LLM-cost**. The LLM-enhanced mode is an optional overlay that provides deeper analysis for users who want it. The interface is designed now so the rule engine can accommodate it cleanly.

### Interface

```bash
# Enable LLM mode
skill-lint --llm path/to/skill/

# With specific model
skill-lint --llm --model sonnet path/to/skill/

# LLM analysis only (skip heuristic rules)
skill-lint --llm-only path/to/skill/
```

### LLM Rules (LLM-*)

| ID | Name | What it analyzes |
|----|------|-----------------|
| LLM-001 | `description-effectiveness` | Predicts activation accuracy: given 10 synthetic prompts (5 should trigger, 5 shouldn't), does the description enable correct classification? |
| LLM-002 | `body-coherence` | Checks if body instructions are internally consistent, non-contradictory, and logically ordered. |
| LLM-003 | `description-body-alignment` | Verifies the description accurately represents what the body instructs. Catches stale descriptions. |
| LLM-004 | `instruction-clarity` | Rates how unambiguous the body instructions are. Flags vague directives ("handle appropriately"). |
| LLM-005 | `trigger-coverage` | Given the skill's domain, suggests missing trigger phrases that would improve activation recall. |

### Integration Architecture

```python
class LLMRule(BaseRule):
    """Base class for LLM-enhanced rules."""

    requires_llm = True

    def run(self, skill_data: SkillData, llm_client: LLMClient) -> list[RuleDiagnostic]:
        """LLM rules receive an LLM client in addition to skill data."""
        ...

class LLMClient(Protocol):
    """Protocol for LLM backends. Pluggable."""

    def complete(self, prompt: str, max_tokens: int = 1024) -> str:
        ...

# Adapters for different backends
class AnthropicClient(LLMClient):
    """Uses Claude via Anthropic API."""
    ...

class OllamaClient(LLMClient):
    """Uses local models via Ollama."""
    ...
```

### LLM Scoring

LLM rules contribute to a separate **LLM Score** (0-50 points) that is displayed alongside the heuristic score but does **not** affect the base 0-100 score. This keeps heuristic scores deterministic and comparable.

```
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Heuristic Score: 82 / 100          Grade: B
  ████████████████████░░░░░           82%

  LLM Score: 41 / 50                 Grade: A
  ████████████████████░░░░░           82%
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Cost Controls

- LLM mode requires explicit opt-in (`--llm`).
- Each LLM rule declares its expected cost (tokens in/out).
- CLI shows estimated cost before running: `"LLM analysis will use ~5K tokens (~$0.02). Continue? [Y/n]"`
- Results are cached in `.skill-lint-cache/` to avoid repeated API calls on unchanged skills.
- `--llm-budget` flag sets a max spend per run.

---

## Appendix A: Full Rule Reference (Quick Lookup)

| ID | Category | Default Severity | Weight | Name |
|----|----------|-----------------|--------|------|
| FM-001 | Frontmatter | error | -10 | missing-skill-md |
| FM-002 | Frontmatter | error | -10 | missing-frontmatter |
| FM-003 | Frontmatter | error | -5 | missing-name |
| FM-004 | Frontmatter | warning | -2 | name-format |
| FM-005 | Frontmatter | error | -5 | missing-description |
| FM-006 | Frontmatter | warning | -2 | description-length |
| FM-007 | Frontmatter | error | -10 | invalid-yaml |
| FM-008 | Frontmatter | info | 0 | unknown-fields |
| DESC-001 | Description | warning | -5 | description-too-short |
| DESC-002 | Description | warning | -3 | description-too-long |
| DESC-003 | Description | info | +3 | description-sweet-spot |
| DESC-004 | Description | warning | -5 | missing-trigger-phrase |
| DESC-005 | Description | info | +3 | has-trigger-phrase |
| DESC-006 | Description | info | -2 | missing-anti-trigger |
| DESC-007 | Description | info | +2 | has-anti-trigger |
| DESC-008 | Description | warning | -4 | high-generic-ratio |
| DESC-009 | Description | info | +2 | low-generic-ratio |
| DESC-010 | Description | warning | -3 | no-dual-audience |
| DESC-011 | Description | info | +2 | has-dual-audience |
| DESC-012 | Description | warning | -2 | description-starts-generic |
| BODY-001 | Body | warning | -5 | body-too-long |
| BODY-002 | Body | error | -10 | body-very-long |
| BODY-003 | Body | warning | -4 | no-headings |
| BODY-004 | Body | info | -2 | few-headings |
| BODY-005 | Body | warning | -3 | no-gotchas-section |
| BODY-006 | Body | info | +3 | has-gotchas-section |
| BODY-007 | Body | info | -2 | no-examples |
| BODY-008 | Body | warning | -3 | inline-dump |
| BODY-009 | Body | warning | -5 | empty-body |
| BODY-010 | Body | info | +2 | has-progressive-disclosure |
| REF-001 | References | error | -4/ea | broken-file-reference |
| REF-002 | References | error | -3/ea | script-not-executable |
| REF-003 | References | warning | -2/ea | broken-relative-link |
| REF-004 | References | warning | -2/ea | unreferenced-script |
| REF-005 | References | info | -1/ea | unreferenced-reference |
| REF-006 | References | info | -1/ea | empty-directory |
| REF-007 | References | info | +5 | all-refs-resolve |
| REF-008 | References | info | +3 | all-scripts-executable |
| REF-009 | References | warning | -1/ea | script-has-shebang |
| COMP-001 | Completeness | info | +2 | has-scripts-dir |
| COMP-002 | Completeness | info | +2 | has-references-dir |
| COMP-003 | Completeness | info | +2 | has-agents-dir |
| COMP-004 | Completeness | info | +3 | has-evals-dir |
| COMP-005 | Completeness | info | +1 | has-assets-dir |
| COMP-006 | Completeness | info | +3 | scripts-documented |
| COMP-007 | Completeness | info | +2 | no-orphan-files |
| COMP-008 | Completeness | info | +1 | has-readme |
| COMP-009 | Completeness | info | +4 | structure-complete |
| BONUS-001 | Bonus | info | +2 | has-version |
| BONUS-002 | Bonus | info | +2 | has-benefits-from |
| BONUS-003 | Bonus | info | +2 | has-allowed-tools |
| BONUS-004 | Bonus | info | +1 | has-license |
| BONUS-005 | Bonus | info | +1 | has-compatibility |
| BONUS-006 | Bonus | info | +2 | has-preamble-tier |

**Total rules: 46** (6 error, 14 warning, 26 info)

---

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **Skill** | A directory containing a SKILL.md file and optional supporting files |
| **Frontmatter** | YAML metadata block at the top of SKILL.md between `---` delimiters |
| **Body** | The markdown content of SKILL.md after the frontmatter |
| **Trigger phrase** | Text pattern in the description that helps the AI decide when to activate |
| **Anti-trigger phrase** | Text pattern that tells the AI when NOT to activate |
| **Progressive disclosure** | Pattern of keeping the body concise and loading references/ on demand |
| **gstack** | Extension framework that adds fields like `preamble-tier`, `version`, `benefits-from` |
| **SARIF** | Static Analysis Results Interchange Format — standard for CI/CD integration |
