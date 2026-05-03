# Testing Guide

This guide explains how to test skills-for-fabric before submitting changes.

## Test Suite Overview

| Test | File | Purpose |
|------|------|---------|
| Quality Checker | `.github/workflows/quality_checker.py` | Structural and semantic validation |
| Skill Catalog Sync | `.github/scripts/generate_skill_catalog.py --check` | Verifies `docs/skill-catalog.md` matches checked-in skill frontmatter |
| Coverage Gap Report | `tests/coverage_gap_report.py` | Advisory audit of smoke / individual / combined eval coverage |
| Coverage Enforcement | `tests/coverage_enforcement.py` | Enforced new-skill ownership + smoke / eval policy with governed allow-missing entries |
| Semantic Tests | `tests/test_semantic.py` | Naming, similarity, description quality |
| Routing Tests | `tests/test_skill_routing.py` | Prompts route to correct skills |

> Current automated tests target `skills/` content. Agent definitions should still be validated manually for routing boundaries, reference integrity, and delegation clarity.

### Smoke Test Principles

Smoke tests (`tests/run-smoke-tests.ps1` → `tests/tests.json`) validate each skill end-to-end against a live Fabric workspace via `copilot --yolo`.

1. **Dynamic test data only.** All test data (lakehouses, tables, notebooks, semantic models, eventhouses) must be provisioned dynamically during test setup — never rely on pre-existing static data. The setup script (`tests/testdata/setup_test_env.py`) creates a fresh, timestamped workspace with all required artifacts so tests are self-contained and reproducible.

2. **Use the shared test tenant only.** All smoke tests must target the tenant configured in the setup script (`E2EAPIMSIT2.onmicrosoft.com`), authenticated via certificate from Azure Key Vault. Do **not** use personal Microsoft tenants or any other environment. Every test prompt should reference the dynamically provisioned workspace name (injected via the `{{WORKSPACE}}` placeholder in `tests.json`), not a hardcoded workspace on a separate tenant.

3. **Fast, single-skill, major-scenario coverage.** Smoke tests must be fast-running and limited to the core scenarios each skill is expected to handle — typically one or two prompts per skill. They should invoke only a single skill per test case. Each smoke test has a hard timeout of **5 minutes** — if a test exceeds this limit, it is automatically failed with a timeout error. Slower, more detailed tests — including multi-skill workflows and cross-skill handoffs — belong in the full eval suite (`tests/full-eval-tests/`), not in smoke.

## Quick Start

### Install Dependencies

```bash
pip install PyYAML requests pytest
```

### Run All Checks

```bash
# Quality checker
python .github/workflows/quality_checker.py

# Skill catalog sync
python .github/scripts/generate_skill_catalog.py --check

# Coverage gap report
python tests/coverage_gap_report.py

# Coverage enforcement
python tests/coverage_enforcement.py --base-ref origin/main

# Fast tests
python -m pytest tests/test_semantic.py -q
python -m unittest tests/test_coverage_gap_report.py tests/test_coverage_enforcement.py tests/test_validation_results_check.py tests/test_skill_ownership_manifest.py -v
```

`tests/coverage_gap_report.py` remains advisory. `tests/coverage_enforcement.py` is the
blocking policy check for new-skill ownership / coverage requirements and for keeping
the current allow-missing baseline governed in `.github/coverage-policy.yml`.

## Contributor pre-merge validation

For a skill PR, these are the current checks contributors should understand before merge:

| Validation | Command / Entry Point | What it tells you | When to use it |
|------------|------------------------|-------------------|----------------|
| Quality checker | `python .github/workflows/quality_checker.py` | Structural, semantic, and reference validation | Every skill PR |
| Skill catalog sync | `python .github/scripts/generate_skill_catalog.py --check` | Whether `docs/skill-catalog.md` is in sync with current skill frontmatter | When skill frontmatter changes |
| Coverage asset audit | `python tests/coverage_gap_report.py` | Whether the repo still sees your skill as missing smoke / individual eval assets | Every skill PR |
| Coverage enforcement | `python tests/coverage_enforcement.py --base-ref origin/main` | Whether new skills satisfy ownership / smoke / eval policy and current gaps are governed | Every skill PR |
| Ownership manifest validation | `python -m unittest tests/test_skill_ownership_manifest.py -v` | Whether `.github/skill-ownership.yml` is in sync | When ownership manifest changes |
| Python tests | `pytest tests/ -v` or targeted test files | Repo test coverage for changed tests / helpers | When tests change |
| Smoke harness | `powershell -File tests\testFabricSkills.ps1 -testName "<smoke-test-name>" -directoryPath C:\temp\fabric-smoke` | Executes a specific smoke scenario from `tests/tests.json` | When smoke coverage is present / updated |
| Full eval suite runner | `powershell -File tests\run-full-tests.ps1 -TestFolder C:\temp\fabric-full-eval` | Runs the current full eval suite and produces result files | When a dedicated eval environment is available or full-suite validation is requested |

Important distinctions:

- `tests/coverage_gap_report.py` is a **report script**, not a behavioral test runner.
- `tests/coverage_enforcement.py` is the **blocking policy check** for new-skill coverage expectations.
- `tests/testFabricSkills.ps1` is the current **manual smoke entry point**.
- `tests/run-full-tests.ps1` is the current **manual full-eval suite runner**.

PR automation now runs a fast validation workflow that covers:

- `quality_checker.py`
- `.github/scripts/generate_skill_catalog.py --check`
- `tests/test_semantic.py`
- `tests/test_coverage_gap_report.py`
- `tests/test_coverage_enforcement.py`
- `tests/test_validation_results_check.py`
- `tests/test_skill_ownership_manifest.py`
- `tests/coverage_enforcement.py`

The workflow also posts one sticky PR summary comment with changed-skill ownership /
smoke / individual / combined coverage status and blocks skill PRs that omit the
required `Validation Results` section.

Contributors should still record validation results in the PR using a text-first
`Validation Results` section:

- manual smoke results when smoke coverage is appropriate
- manual individual-eval results for new skills or material behavior changes
- manual combined-eval results only for paired / handoff workflows

For each row, include the exact command or eval plan used, `PASS` / `FAIL` / `N/A`,
and a short summary. Logs / pasted output are preferred; screenshots are optional
supporting artifacts.

## Quality Checker

The quality checker (`quality_checker.py`) validates every skill in `skills/`:

### What It Checks

| Category | Checks |
|----------|--------|
| **Structure** | YAML frontmatter, name/description fields, update notice |
| **Content** | Must/Prefer/Avoid sections, examples, code block tags |
| **Semantics** | Trigger uniqueness, description similarity (Jaccard) |
| **References** | Cross-reference link validation |
| **Quality** | Description starts with action verb, mentions technologies |

### Running Locally

```bash
python .github/workflows/quality_checker.py
```

### Sample Output

```
📋 skills-for-fabric QUALITY CHECK
==================================================

📂 Scanning: check-updates
📂 Scanning: spark-authoring-cli
📂 Scanning: sqldw-authoring-cli

🔄 Running cross-skill analysis...

==================================================
📊 QUALITY CHECK SUMMARY
Files scanned: 5
Critical issues: 0
Warnings: 2

⚠️  Semantically ambiguous triggers: 2

   | Trigger Phrase | Matches These Skills                    | Ambiguity |
   |----------------|----------------------------------------|-----------|
   | run sql        | spark-consumption-cli, sqldw-consumption-cli | 2 skills |

✅ RESULT: PASSED with 2 warning(s)
📄 Report saved to: quality-report.json
```

### Understanding Results

| Status | Meaning | Action |
|--------|---------|--------|
| `PASSED` | All checks passed | Ready to submit |
| `PASSED with warnings` | Non-blocking issues found | Review and consider fixing |
| `CRITICAL` | Blocking issues found | Must fix before merge |

## Pytest Tests

### Test Categories

```bash
# Run all tests
pytest tests/ -v

# Run only semantic tests
pytest tests/test_semantic.py -v

# Run only routing tests
pytest tests/test_skill_routing.py -v

# Run by marker
pytest tests/ -v -m semantic
pytest tests/ -v -m routing
```

### Semantic Tests (`test_semantic.py`)

Validates skill semantics:

| Test Class | Purpose |
|------------|---------|
| `TestTriggerUniqueness` | No duplicate triggers, ambiguous triggers have qualifiers |
| `TestDescriptionSimilarity` | Jaccard similarity < 30% between skills |
| `TestNamingConventions` | Names follow `{endpoint}-{authoring|consumption|monitoring}-cli` pattern |
| `TestDescriptionQuality` | Descriptions start with action verbs, mention technologies |

### Routing Tests (`test_skill_routing.py`)

Validates that user prompts route to the correct skill:

```python
@pytest.mark.parametrize("prompt", [
    "show me all tables in my warehouse",
    "query my warehouse to get top 10 products",
    "run a T-SQL query against Fabric",
])
def test_routes_to_sql_consumption(self, prompt, all_skills):
    """Prompt should route to sqldw-consumption-cli."""
    skill, score = route_prompt(prompt, all_skills)
    assert skill == "sqldw-consumption-cli"
```

### Adding New Routing Tests

When adding a new skill, add routing tests:

```python
# tests/test_skill_routing.py

@pytest.mark.routing
class TestMyNewSkillRouting:
    """Test prompts that should route to my-new-skill."""
    
    @pytest.mark.parametrize("prompt", [
        "prompt that should trigger my skill",
        "another triggering prompt",
    ])
    def test_routes_to_my_skill(self, prompt, all_skills):
        """Prompt should route to my-new-skill."""
        skill, score = route_prompt(prompt, all_skills)
        assert skill == "my-new-skill"
```

## Pre-commit Hook

### Installation

```bash
# Windows (PowerShell)
Copy-Item .github\hooks\pre-commit .git\hooks\pre-commit

# macOS/Linux
cp .github/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### What It Does

Before each commit, the hook:

1. Runs the quality checker on changed skill files
2. Blocks commit if critical issues are found
3. Shows warnings but allows commit

### Bypassing (Not Recommended)

```bash
git commit --no-verify -m "message"
```

## CI/CD Workflow

### Pull Request Checks

When you push a PR that changes skills or the validation pipeline:

1. **Skill PR Validation** (`quality-check.yml`)
   - Runs quality checker, semantic/unit tests, ownership validation, and coverage enforcement
   - Posts one sticky PR validation summary comment
   - Uploads `quality-report.json` and `coverage-enforcement.json` as artifacts

2. **Security Audit** (`security-audit.yml`)
   - Scans for secrets and sensitive data
   - Validates security guidelines
   - Uploads `security-report.json` as an artifact without adding extra PR comment noise

3. **Daily Coverage Gap Report** (`daily-coverage-gap-report.yml`)
   - Runs `tests/coverage_gap_report.py` on a daily schedule
   - Uploads `coverage-gap-report.json` as a workflow artifact
   - Can also be triggered manually with `workflow_dispatch`

> Fast PR automation still does **not** execute manual smoke or full-eval workflows for
> you. Record the relevant manual evidence in the PR whenever the change needs it.

### Workflow Triggers

```yaml
on:
  pull_request:
    branches: [ main, master ]
    paths:
      - 'skills/**/*.md'
      - '.github/coverage-policy.yml'
      - '.github/skill-ownership.yml'
      - '.github/workflows/*.py'
      - '.github/workflows/*.yml'
      - 'tests/**/*.md'
      - 'tests/**/*.py'
      - 'tests/tests.json'
  push:
    branches: [ main, master ]
    paths:
      - 'skills/**/*.md'
      - '.github/coverage-policy.yml'
      - '.github/skill-ownership.yml'
      - '.github/workflows/*.py'
      - '.github/workflows/*.yml'
      - 'tests/**/*.md'
      - 'tests/**/*.py'
      - 'tests/tests.json'
```

Scheduled coverage reporting is separate:

```yaml
on:
  schedule:
    - cron: '0 12 * * *'
  workflow_dispatch:
```

## Testing Locally with Copilot CLI

### Symlink Your Skill

```bash
# Windows (PowerShell as Admin)
New-Item -ItemType SymbolicLink `
  -Path "$env:USERPROFILE\.copilot\skills\my-new-skill" `
  -Target ".\skills\my-new-skill"

# macOS/Linux
ln -s $(pwd)/skills/my-new-skill ~/.copilot/skills/my-new-skill
```

### Verify Loading

Start a new Copilot CLI session:

```
/skills list
```

Your skill should appear in the list.

### Test Prompts

Try prompts that should trigger your skill and verify correct routing.

## Test File Structure

```
tests/
├── conftest.py              # Shared fixtures (all_skills, etc.)
├── README.md                # Test documentation
├── requirements-dev.txt     # Test dependencies
├── test_semantic.py         # Semantic validation tests
└── test_skill_routing.py    # Routing tests
```

### Shared Fixtures (`conftest.py`)

```python
@pytest.fixture
def all_skills():
    """Load all skills from skills/ folder."""
    skills = {}
    skills_dir = Path(__file__).parent.parent / "skills"
    
    for skill_folder in skills_dir.iterdir():
        skill_md = skill_folder / "SKILL.md"
        if skill_md.exists():
            # Parse frontmatter and add to skills dict
            ...
    
    return skills
```

## Debugging Test Failures

### Quality Checker Failures

1. Read the specific error message
2. Check `quality-report.json` for details
3. Common fixes:
   - Add missing frontmatter fields
   - Add update notice
   - Tag code blocks with language
   - Fix broken cross-references

### Routing Test Failures

```
AssertionError: Expected sqldw-consumption-cli but got spark-consumption-cli
```

1. Check your skill's triggers in the description
2. Add more specific trigger phrases
3. Ensure triggers don't overlap with other skills

### Semantic Test Failures

```
Skills with similarity >= 30%: [{'skills': ('skill-a', 'skill-b'), 'similarity': 35.2}]
```

1. Differentiate descriptions between the two skills
2. Use more specific terminology
3. Clarify distinct use cases

## Best Practices

1. **Run tests before every commit** — Use the pre-commit hook
2. **Add routing tests for new skills** — Verify correct routing
3. **Check quality report** — Review `quality-report.json` for details
4. **Test locally first** — Don't rely only on CI/CD
5. **Keep tests updated** — When adding triggers, add corresponding tests

## Next Steps

- [Quality Requirements](quality-requirements.md) — What the tests check
- [Skill Authoring Guide](skill-authoring-guide.md) — How to create skills
