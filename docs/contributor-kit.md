# Contributor Kit

This guide is the practical checklist for adding or changing skills in `skills-for-fabric`.
Use it together with:

- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [Skill Authoring Guide](skill-authoring-guide.md)
- [Testing Guide](testing-guide.md)

## Required artifacts for skill work

Every contributor-facing skill change should consider these five artifacts:

1. **Skill content**
   - `skills/{name}/SKILL.md`
   - Any `references/` or `resources/` files needed by the skill

2. **Ownership metadata**
   - `.github/skill-ownership.yml`
   - Every checked-in skill must have one ownership entry

3. **Coverage policy metadata**
   - `.github/coverage-policy.yml`
   - Update this only when you add an explicit coverage exemption or pay down tracked coverage debt

4. **Fast validation coverage**
   - A smoke test case when the skill should be sanity-checked quickly

5. **Eval coverage**
   - An individual eval plan for the skill
   - A combined eval update only when the change participates in a documented paired or handoff workflow

## Ownership manifest

The ownership manifest lives at:

```text
.github/skill-ownership.yml
```

The manifest is the repository source of truth for **who owns what inside this repo**.
Its `owningTeam` values are repository ownership buckets. They do not need to match GitHub
teams or Azure AD groups one-to-one.

### Example entry

```yaml
skills:
  sqldw-authoring-cli:
    owningTeam: sqldw
    area: authoring
```

### When to update it

Update `.github/skill-ownership.yml` when you:

- add a new skill
- rename a skill
- move a skill between ownership buckets
- split one skill into multiple skills

## Coverage expectations

The enforced coverage policy lives at:

```text
.github/coverage-policy.yml
```

Use it to track the current repo baseline of allowed-missing coverage and any explicit
coverage exemptions. New skills should not add `status: debt`; either add the missing
asset or record a justified `status: exempt`.

### Smoke coverage

Add or update smoke coverage when the skill should have a quick sanity check in the fast path.

### Individual eval coverage

Add or update an individual eval when the skill's core behavior changes or when a new skill is introduced.

### Combined eval coverage

Combined eval is **not automatic for every skill**.
Add or update combined eval only when the skill participates in a real multi-skill handoff or paired workflow that the repo intends to support.

## Commands to run locally

```bash
python .github/workflows/quality_checker.py
python .github/scripts/generate_skill_catalog.py --check
python tests/coverage_gap_report.py
python tests/coverage_enforcement.py --base-ref origin/main
python -m unittest tests/test_skill_ownership_manifest.py -v
pytest tests/ -v
```

## Validation Results section for manual evidence

PR automation now enforces the fast checks (quality, skill catalog sync, semantic/unit
tests, ownership sync, the `Validation Results` section for skill PRs, and new-skill
coverage policy), but contributors still need to record manual smoke / eval evidence
in the PR when the workflow cannot run those scenarios itself.
Use a text-first `Validation Results` section in the PR body or one dedicated PR
comment so humans and LLMs can review it easily later.

The sticky PR summary comment now reports the automated checks. In the PR body or a
dedicated PR comment, record only the manual evidence that CI cannot produce.

### Required PR manual results

1. **Manual smoke results**
     - Required when smoke coverage is appropriate for the skill.
     - Current smoke harness:

```powershell
powershell -File tests\testFabricSkills.ps1 -testName "<smoke-test-name>" -directoryPath C:\temp\fabric-smoke
```

2. **Manual individual-eval results**
     - Required for new skills and material behavior changes.
     - Use the relevant plan under `tests/full-eval-tests/plan/03-individual-skills/`.
    - If you use the suite runner, the current command is:

```powershell
powershell -File tests\run-full-tests.ps1 -TestFolder C:\temp\fabric-full-eval
```

    - If you do not run the full suite, record the manual prompt steps and outputs that satisfy the individual eval plan.

3. **Manual combined-eval results**
     - Required only when the PR changes a documented paired or handoff workflow.

### Recommended PR format

Record the results in a short markdown table:

```md
## Validation Results

| Check | Command / Plan | Result | Notes / Artifact |
|---|---|---|---|
| Smoke | `powershell -File tests\testFabricSkills.ps1 ...` | PASS | `testName: ...` |
| Individual eval | `tests/full-eval-tests/plan/03-individual-skills/eval-...` | PASS | short summary |
| Combined eval | `tests/full-eval-tests/plan/04-combined-skills/...` | PASS / N/A | short summary |
```

For manual smoke or eval rows, include:

- the exact smoke test name or eval plan path
- `PASS`, `FAIL`, or `N/A`
- a short summary
- logs / pasted output when practical
- screenshots only as optional supporting artifacts

## Suggested PR shape

For a new skill or a meaningful behavior change, a good PR usually includes:

1. skill content updates
2. ownership manifest update
3. coverage policy update if you add an explicit exemption or remove tracked debt
4. smoke coverage update
5. individual eval update
6. combined eval update if the workflow is paired/handoff-based
7. structured validation results in the PR
8. documentation updates if contributor expectations changed

## Reviewer checklist

Reviewers should be able to answer:

- Does the ownership manifest include this skill?
- Is the owning team bucket reasonable?
- If the skill is intentionally missing smoke or eval coverage, is that reflected in `.github/coverage-policy.yml` with a clear reason?
- Is smoke coverage present when a fast sanity check is appropriate?
- Is individual eval coverage present for the changed behavior?
- If the PR changes a paired workflow, was combined eval considered?
- Does the PR include a structured `Validation Results` section for the required manual evidence?
