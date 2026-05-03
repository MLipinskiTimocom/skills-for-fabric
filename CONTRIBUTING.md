# Contributing to Fabric Skills

Thank you for your interest in contributing to Microsoft Fabric Skills!

## Quick Start

### Fork & Branch

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/<your-username>/skills-for-fabric.git
   cd skills-for-fabric
   ```
3. **Create a dedicated branch** for your contribution:
   ```bash
   git checkout -b <your-branch-name>   # e.g., add-realtime-authoring-skill
   ```
4. Make your changes, test locally, then push and open a PR against `main`.

> Do **not** commit directly to `main` in your fork. Always work on a feature branch so the PR diff stays clean and reviewable.

### Learn the Repo

1. Read the **[Skill Authoring Guide](docs/skill-authoring-guide.md)** — comprehensive how-to
2. Read the **[Contributor Kit](docs/contributor-kit.md)** — ownership + coverage expectations
3. Read the **[Testing Guide](docs/testing-guide.md)** — exact local commands, smoke harness, and full-eval runner
4. Review the **[Quality Requirements](docs/quality-requirements.md)** — what makes a good skill
5. Check the **[Skill Catalog](docs/skill-catalog.md)** — see existing skills as examples

### EXAMPLE:  **[Create a new skill](prompt_examples/skills-creator/CreateAFabricSkill.txt)** — see how to use CLI to create a skill


## Scope of Contributions

**Skills only** — The agent definitions under `agents/` are **fixed** and maintained by the core team. Do not create, rename, or modify agent files. All contributions should focus on **skills** (under `skills/`) and their supporting documentation.

If you believe an agent change is needed, open an issue describing the gap and the team will evaluate it.

## Skill Category Governance

### Approved Categories

All skills MUST belong to one of the three approved skill categories:

| Category | Naming Pattern | Purpose |
|----------|---------------|---------|
| **Authoring** | `{endpoint}-authoring-{access_method}` | Developer workflows — DDL/DML, CI/CD, SDK, deployment |
| **Consumption** | `{endpoint}-consumption-{access_method}` | Interactive data exploration — read-only queries, schema discovery, ad-hoc analysis |
| **Operations** | `{endpoint}-operations-{access_method}` | Workload operator workflows — monitoring, diagnostics, performance investigation, system views, DMVs, troubleshooting within a single workload |

> **What does the `{access_method}` slot mean?** It is the third segment of the full pattern `{endpoint}-{category}-{access_method}` and identifies *how* the skill drives Fabric. Today every shipping skill uses `cli` — meaning the skill drives Fabric through command-line tools (`az rest`, `az login`, `sqlcmd`, `curl`, `jq`) and delegates auth/tooling to [`common/COMMON-CLI.md`](common/COMMON-CLI.md).
>
> The slot is a **discriminator**, not decoration. It exists so the same endpoint and category can ship parallel skills for other access methods later — e.g., `sqldw-authoring-sdk` (Fabric Python/.NET SDK), `sqldw-authoring-mcp` (MCP server tools), or `sqldw-authoring-portal` (Fabric portal walk-throughs). Do not invent new access-method values without first adding the corresponding `common/` documentation and updating the validators.

New skills MUST fit within one of these three categories. Do **not** create skills in other categories (e.g., security, migration, upgrade, GPU acceleration) without explicit approval from the core team.

> **Operations is the workload-operator category.** Concerns like **monitoring**, **diagnostics**, **performance tuning**, and **troubleshooting** within a single workload fall under Operations. The persona is the **workload operator** — typically the same developer who authored the workload, now investigating its runtime behavior (not a tenant or capacity admin).
>
> **Tenant, workspace, and capacity administration do NOT belong in workload categories.** Cross-workload governance work (tenant settings, capacity management, workspace-level policies, cross-workload security governance) belongs in the **`FabricAdmin` agent** (`agents/FabricAdmin.agent.md`), which is maintained by the core team. Workload teams must not create or modify agent files directly — if your scenario needs the `FabricAdmin` agent extended, open an issue describing the gap and the core team will evaluate it. If you're tempted to create a `{endpoint}-admin-cli`, stop and ask whether the work is actually tenant/workspace-level — if yes, file a request against `FabricAdmin` instead.
>
> **Known exceptions — project-shaped skills.** Migration skills (`databricks-migration`, `hdinsight-migration`, `synapse-migration`) do not follow the three-category pattern because they are one-time, project-scoped workflows rather than ongoing workload interactions. New project-shaped skills (e.g., upgrade flows) may be proposed as named top-level skills, but require the same governance bar as a new category.

### Why Three Categories

Constraining to three categories is a deliberate governance decision, not a technical limitation:

1. **Context window discipline** — Every additional skill consumes LLM context. Uncontrolled growth degrades model quality for all users, not just the new skill's audience.
2. **Platform cost** — Each skill adds overhead in plugin registration, marketplace metadata, and folder management. The cost compounds across the ecosystem.
3. **Collection-based installation** — Most users install the full skill collection. Internally, skills are structured into categories for hygiene; externally, the collection is opaque. Adding categories does not improve the end-user experience for 99% of users.
4. **Intentional design over reactive creation** — Skills must be designed with purpose, not created reactively because an upstream team requests one. The bar is: *"Can we achieve the same outcome without a new skill? Show that it's not possible."*

### Proposing a New Category

If you believe a scenario genuinely cannot be served by Authoring, Consumption, or Operations:

1. Open an issue with the title `[New Category Proposal]: {name}`
2. Include:
   - **Scenario description** — What user problem does this solve?
   - **Proof of insufficiency** — Demonstrate that the existing three categories cannot cover this scenario (include example prompts and expected vs. actual behavior)
   - **Impact assessment** — How many skills would this category add? What is the context window cost?
3. The core team will review. Approval requires demonstrating a clear functional gap, not just organizational convenience.

### Specialization via Compound Endpoints

If a scenario needs specialization (e.g., SQL security, GPU acceleration), the preferred pattern is a **compound-endpoint skill** that still fits within the three categories:

```
{endpoint}-{specialization}-{authoring|consumption|operations}-{access_method}
```

**Examples:**
- `sqldw-security-authoring-cli` — SQL security authoring workflows (CLI access)
- `spark-gpu-authoring-cli` — GPU-accelerated Spark authoring (CLI access)

This is preferred over:
- ❌ A new top-level category (e.g., `sqldw-security-cli` as a 4th category)
- ❌ A sub-skill concept (not a shipped platform feature)

compound-endpoint skills must still pass the same bar as any new skill:

1. **Minimum 5 eval prompts** covering the specialization's distinct behaviors
2. **Baseline validation** proving the existing parent skill (e.g., `sqldw-authoring-cli`) cannot handle these prompts adequately
3. **Jaccard check** against sibling skills — especially the parent endpoint (e.g., `sqldw-authoring-cli`) where trigger overlap is most likely
4. **Ownership clarity** in `.github/skill-ownership.yml` — the specialization team owns the compound skill, separate from the parent endpoint team

If the baseline test shows the parent skill already handles the prompts well, the compound skill is not needed — add the content to the parent instead.

## Key Guidelines (Summary)

For detailed documentation, see the `docs/` folder. Here's the quick summary:

### Skill Structure

Each skill lives in its own folder under `skills/` with a `SKILL.md` file.

```
skills/my-skill/
├── SKILL.md              # Required
└── references/           # Optional
```

### Naming Convention

- **Developer skills**: `{endpoint}-authoring-{access_method}` (e.g., `sqldw-authoring-cli`)
- **Consumer skills**: `{endpoint}-consumption-{access_method}` (e.g., `sqldw-consumption-cli`)
- **Operations skills**: `{endpoint}-operations-{access_method}` (e.g., `sqldw-operations-cli`)
- **Agents** (core team only, not contributor-authored): `{persona}` (e.g., `FabricDataEngineer`, `FabricAdmin`) for cross-endpoint orchestration — workload teams must not add or modify these

### What Goes Where

| Content Type | Location | Editable by | See Guide |
|--------------|----------|-------------|-----------|
| Agent definition | `agents/{persona}.agent.md` | Core team only | [Architecture Overview](docs/architecture-overview.md) |
| Skill definition | `skills/{name}/SKILL.md` | Contributors | [Skill Authoring](docs/skill-authoring-guide.md) |
| Shared reference docs | `common/` | Core team only | [Common Folder](docs/common-folder-guide.md) |
| Plugin manifest (`skills` / `mcpServers` arrays of existing plugins) | `plugins/<name>/.github/plugin/plugin.json` | Contributors (existing plugins only) | [Plugins](docs/plugins-guide.md) |
| Creating a new plugin | `plugins/<new-name>/...` | Core team only — file an issue | [Plugins](docs/plugins-guide.md) |
| Marketplace files | `.claude-plugin/marketplace.json`, `.github/plugin/marketplace.json` | **Auto-generated** by `python build/build_plugins.py` from per-plugin manifests | [Plugins](docs/plugins-guide.md) |
| Marketplace-level metadata (collection name, owner) | `build/marketplace.config.json` | Core team only | [Plugins](docs/plugins-guide.md) |
| MCP server config | `mcp-setup/` and `mcpServers` block in plugin manifests | Contributors (when their skill needs one) | [MCP Servers](docs/mcp-servers-guide.md) |

### Plugin Manifest Update (Required For New Skills)

Adding a skill to `skills/` is not enough — it must also be referenced from at least one plugin manifest, otherwise it does not ship to users.

When you add a new skill, edit the relevant plugin manifest(s) per this routing table:

| Skill suffix | Add `"./skills/<name>"` to these manifests |
|---|---|
| `-authoring-cli` | `plugins/fabric-authoring/.github/plugin/plugin.json` **and** `plugins/fabric-skills/.github/plugin/plugin.json` |
| `-consumption-cli` | `plugins/fabric-consumption/...` **and** `plugins/fabric-skills/...` |
| `-operations-cli` | `plugins/fabric-operations/...` **and** `plugins/fabric-skills/...` |
| `e2e-*` (cross-workload) | `plugins/fabric-skills/...` and the relevant axis if applicable |
| Migration / project-shaped (sanctioned exceptions) | `plugins/fabric-skills/...` only |

Always include `fabric-skills` (the union bundle) in addition to the axis plugin. Forgetting the union is the most common contribution mistake.

After editing the manifest(s), **run the build** — this regenerates the marketplace files and materializes the plugin trees so you can install locally:

```bash
python build/build_plugins.py
```

The build does two things:

1. **Materializes** `plugins/<name>/{skills,agents,common,.mcp.json}` (gitignored — used for local install testing).
2. **Regenerates** `.github/plugin/marketplace.json` and `.claude-plugin/marketplace.json` from your manifest changes (committed, byte-identical, kept in sync automatically).

**You must commit the regenerated marketplace files** along with your manifest change. Do **not** edit the marketplace files by hand — your edits will be reverted on the next build.

#### Test the plugin locally

After running the build, install your repo as a local marketplace and verify your skill shows up:

```bash
# In Copilot CLI / Claude Code, register this repo as a marketplace
/plugin marketplace add D:\FabricSkills

# Browse the collection — your new skill should appear under the right plugin
/plugin marketplace browse fabric-collection

# Install the plugin you added the skill to
/plugin install fabric-authoring@fabric-collection
```

If your skill does **not** show up in `browse`, you forgot to re-run `python build/build_plugins.py` after editing the manifest — the marketplace was not regenerated.

#### Clean up the materialized plugin trees

The build writes `plugins/<name>/{skills,agents,common,.mcp.json}` for local install. These are gitignored, but you can delete them when you're done testing to keep your working tree tidy:

```bash
python build/build_plugins.py --purge
```

This removes only the materialized content. Manifests, marketplace files, and tracked files are untouched.

See [docs/plugins-guide.md](docs/plugins-guide.md) for full details.

### What to Avoid

- ❌ Executable scripts or implementation code in skills (use guidance and principles instead)
- ❌ Skills over 15,000 tokens (split or move content to common/)
- ❌ Overlapping trigger phrases with other skills
- ❌ Vague descriptions without action verbs or technologies
- ❌ Code templates that users copy-paste (enable LLM to generate code on-demand)
- ❌ **Creating or modifying agent files** — agents are fixed; contribute skills only

See: [Quality Requirements](docs/quality-requirements.md)

### Delegate Authentication & Tooling to Common

Skills must **not** include their own authentication flows, token acquisition logic, or tool installation instructions. These concerns are handled centrally in [COMMON-CLI.md](common/COMMON-CLI.md) and [COMMON-CORE.md](common/COMMON-CORE.md).

Specifically, do **not** embed any of the following inside a skill:

| Topic | Where it belongs |
|-------|------------------|
| Azure CLI login / `az login` | [COMMON-CLI.md](common/COMMON-CLI.md) |
| Token acquisition (`az account get-access-token`) | [COMMON-CLI.md](common/COMMON-CLI.md) |
| `az rest` patterns and `--resource` usage | [COMMON-CLI.md](common/COMMON-CLI.md) |
| `sqlcmd` setup and connection strings | [COMMON-CLI.md](common/COMMON-CLI.md) |
| Tool install commands (e.g., `pip install`, `npm install`, download links) | [COMMON-CLI.md](common/COMMON-CLI.md) |
| Workspace/item resolution via REST | [COMMON-CORE.md](common/COMMON-CORE.md) |

Instead, reference the common documentation in your skill's **Prerequisite Knowledge** section:

```markdown
## Prerequisite Knowledge

Read these companion documents:

- [COMMON-CORE.md](../../common/COMMON-CORE.md) — Fabric REST API patterns, auth
- [COMMON-CLI.md](../../common/COMMON-CLI.md) — CLI implementation (az, sqlcmd, curl, jq)
```

This keeps authentication consistent across all skills and avoids divergent solutions.

### Multi-Skill Contributions

When a PR introduces or modifies **more than one skill**, you must verify that the skills are sufficiently distinct:

1. **Run the Jaccard similarity check** between every pair of affected skills:
   ```bash
   python .github/workflows/quality_checker.py
   ```
   The quality checker reports Jaccard similarity scores for all skill-pair descriptions. For your changed skills, confirm:
   - **< 20%** — Good, no action needed
   - **20–30%** — Review and consider differentiating descriptions
   - **≥ 30%** — Must differentiate before merge (Critical)

2. **Differentiate overlapping descriptions** by adding technology qualifiers, persona distinctions, or endpoint specifics. See [Quality Requirements — Jaccard](docs/quality-requirements.md) for examples.

3. **Document the similarity scores** in the PR's `Validation Results` table so reviewers can verify.

## Minimum Evaluation Prompts

### Requirement

Every skill MUST be submitted with **at least 5 evaluation prompts**. These prompts:

- Are stored in the skill's individual eval plan under `tests/full-eval-tests/plan/03-individual-skills/`
- Are executed **nightly** via the full evaluation suite (`tests/run-full-tests.ps1`) to track performance over time
- Must cover the skill's core scenarios (not just happy-path trivial cases)

### Baseline Validation (No-Skill Test)

Before submitting a new skill, you MUST validate that the **evaluation prompts fail or produce inferior results without the skill loaded**. This proves the skill adds genuine value.

**Process:**

1. **Run prompts without the skill**: Remove or unlink the skill from your local environment, then run each of the 5+ evaluation prompts against the base agent (no skill loaded).
2. **Record baseline results**: Document what the model produces without the skill — incorrect output, missing context, hallucinated APIs, or generic responses.
3. **Run prompts with the skill**: Re-enable the skill and run the same prompts.
4. **Document the delta**: In the PR's `Validation Results` section, include a comparison showing how the skill improved the output.

If the model already handles the prompts well without the skill, the skill is not needed. This is the practical application of the governance bar: *"Show me that it's not possible to do without a skill."*

### Eval Prompt Quality

Each evaluation prompt must include:

| Field | Description |
|-------|-------------|
| **Case ID** | Unique identifier (e.g., `SA-01`) |
| **Prompt** | The exact user prompt to send |
| **Expected Result** | What a correct response looks like |
| **Pass Criteria** | Objective criteria for pass/fail |

See existing eval plans in `tests/full-eval-tests/plan/03-individual-skills/` for examples.

## Testing Your Skill Locally

> **Mandatory**: You must test your skill locally **before** opening a PR.
> PRs that fail basic quality or coverage checks will be sent back for revision.
> Additionally, all merged PRs are validated **nightly** via the full evaluation suite
> (`tests/run-full-tests.ps1`). Regressions discovered in nightly runs must be
> fixed promptly by the skill owner.

### Install Pre-commit Hook (Recommended)

Install the pre-commit hook to run quality and security checks automatically before each commit:

```bash
# Windows (PowerShell)
Copy-Item .github\hooks\pre-commit .git\hooks\pre-commit

# macOS/Linux
cp .github/hooks/pre-commit .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

The hook runs on your machine (Windows/Linux/Mac) and blocks commits with critical issues.

### GitHub Copilot CLI

There are two ways to test a skill locally — use both at different stages.

**1. Symlink the canonical skill (fast iteration on content):**

```bash
# Windows
New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.copilot\skills\{skill-name}" -Target ".\skills\{skill-name}"

# macOS/Linux
ln -s $(pwd)/skills/{skill-name} ~/.copilot/skills/{skill-name}
```

Use this while iterating on `SKILL.md` content. Edits take effect on the next session.

**2. Install through the materialized plugin (validates manifest + plugin shape — required before PR):**

```bash
python build/build_plugins.py --clean
```

This materializes `plugins/<plugin>/{skills,agents,common,.mcp.json}` on disk (gitignored). Then point your CLI at the plugin folder, e.g. for Copilot CLI dev:

```
/plugin install file://<repo-root>/plugins/fabric-authoring
```

Use this once before opening the PR. It is the only test that catches a missing manifest entry — the symlink path bypasses plugins entirely.

Then start a new Copilot CLI session and test prompts that should trigger your skill.

### Verifying Skill Loading

In Copilot CLI, you can check which skills are loaded:

```
/skills list
```

## Cross-Tool Compatibility

When adding a new skill or agent, update these compatibility files if needed:

- `compatibility/CLAUDE.md` - Add skill reference
- `compatibility/.cursorrules` - Add relevant rules
- `compatibility/AGENTS.md` - Add for Codex/Jules
- `compatibility/.windsurfrules` - Add for Windsurf

## Pull Request Checklist

- [ ] **Pre-PR testing passed** (quality checker, coverage audit, pytest — see [Testing Your Skill Locally](#testing-your-skill-locally))
- [ ] **Skill category compliance** — skill belongs to Authoring, Consumption, or Operations (see [Skill Category Governance](#skill-category-governance))
- [ ] Skill folder and `SKILL.md` created
- [ ] **Plugin manifest(s) updated** — skill added to the appropriate `plugins/<name>/.github/plugin/plugin.json` per the [routing table](#plugin-manifest-update-required-for-new-skills); `python build/build_plugins.py` succeeds locally
- [ ] **Regenerated marketplace files committed** — the build updates `.github/plugin/marketplace.json` and `.claude-plugin/marketplace.json`; commit those changes alongside your manifest edits
- [ ] `.github/skill-ownership.yml` updated for every added/renamed/moved skill
- [ ] `.github/coverage-policy.yml` updated if a new coverage exemption is added or tracked debt is paid down
- [ ] **No agent files modified** — agents under `agents/` are core-team-owned; gaps must be raised via issue, not PR
- [ ] **No `common/` files modified** — `common/` is core-team-owned; coordinate via issue for changes
- [ ] **Marketplace files NOT hand-edited** — they are generated from per-plugin manifests by `build/build_plugins.py`; manual edits will be reverted
- [ ] Description is clear and discoverable
- [ ] Reference documentation links are valid
- [ ] At least one example provided
- [ ] **Minimum 5 eval prompts** submitted in `tests/full-eval-tests/plan/03-individual-skills/`
- [ ] **Baseline validation** — prompts tested without the skill to confirm the skill adds value (delta documented in PR)
- [ ] Tested locally with Copilot CLI
- [ ] Smoke coverage added/updated when a fast sanity check is appropriate
- [ ] Individual eval coverage added/updated for new or changed skill behavior
- [ ] Combined eval considered for paired or handoff workflows
- [ ] Manual smoke results recorded in the PR `Validation Results` section when smoke coverage is appropriate
- [ ] Manual individual-eval results recorded in the PR `Validation Results` section for new or changed skill behavior
- [ ] Manual combined-eval results recorded in the PR `Validation Results` section for paired or handoff workflows (if applicable)
- [ ] **No auth/tooling embedded in skill** — authentication, tokens, `sqlcmd`, `az rest` patterns delegate to `common/`
- [ ] **Jaccard check passed** for multi-skill PRs (all pairs < 30% similarity)
- [ ] Updated compatibility files (if applicable)
- [ ] Updated `CHANGELOG.md` with your changes (see below)
- [ ] Updated relevant specs/docs if behavior changed (see `docs/`)
- [ ] **Security**: No hardcoded secrets or credentials
- [ ] **Security**: Reviewed against docs/RAI_THREAT_MODEL.md
- [ ] **Security**: Added tests for prompt injection resistance (if applicable)

## Automated Quality Checks

When you submit a PR that modifies files in `skills/`, an automated quality check runs. The check validates:

### Critical Issues (Block PR)

| Check | Description |
|-------|-------------|
| **YAML Frontmatter** | Must have `name` and `description` fields |
| **Update Notice** | Must include the update check blockquote (except `check-updates`) |
| **Description Length** | Frontmatter description must stay within the check-in limit |
| **Encoding Integrity** | Skill markdown files must be valid UTF-8 and free of high-confidence mojibake markers |
| **Common-Infra Compliance** | Generic auth/token/sqlcmd guidance must reference the shared `common/` docs |
| **Cross-References** | All relative links must point to existing files |
| **Trigger Uniqueness** | Trigger phrases must not conflict with other skills |
| **Semantic Disambiguation** | Descriptions must not overlap >30% with other skills |

Other guidance, including the recommended workspace/item discovery instructions, is
still part of the authoring standard but is not yet a separate blocking check in the
quality checker.

### Warnings (Review Recommended)

| Check | Description |
|-------|-------------|
| **Must/Prefer/Avoid Sections** | Should include guidance sections |
| **Examples** | Should include code or prompt/response examples |
| **Code Block Tags** | All code blocks should have language tags (```bash, ```sql, etc.) |
| **Description Quality** | Should start with action verb, mention technologies |
| **Naming Convention** | Should follow `{endpoint}-authoring-{access}`, `{endpoint}-consumption-{access}`, or `{endpoint}-operations-{access}` pattern |
| **External Links** | URLs should be accessible (sampled, rate-limited) |

### Running Locally

Test your skill before submitting. For the full command matrix and the distinction
between the asset audit, smoke harness, and full-eval runner, see the
**[Testing Guide](docs/testing-guide.md)**.

```bash
# Install dependencies
pip install PyYAML requests pytest

# Run quality check
python .github/workflows/quality_checker.py

# Verify plugin manifests resolve (catches typos, missing common refs, forgotten union-bundle entry)
python build/build_plugins.py

# Audit smoke / eval asset coverage
python tests/coverage_gap_report.py

# Enforce new-skill ownership / coverage policy
python tests/coverage_enforcement.py --base-ref origin/main

# Validate ownership manifest coverage
python -m unittest tests/test_skill_ownership_manifest.py -v

# Check generated skill catalog drift when skill frontmatter changes
python .github/scripts/generate_skill_catalog.py --check

# Run repo tests (or the specific test files you changed)
pytest tests/ -v
```

### Manual validation evidence in the PR

Automated PR validation now covers quality checker, skill catalog sync, semantic/unit tests,
ownership validation, coverage enforcement, the required `Validation Results` section for
skill PRs, and the sticky summary comment. The PR `Validation Results` section should focus
on manual smoke / eval evidence and any other non-automated checks.
If you are unsure which command applies, use the **[Testing Guide](docs/testing-guide.md)**
as the source of truth for the current runners.

Use this structure so reviewers and LLMs can read it quickly and search it later:

```md
## Validation Results

| Check | Command / Plan | Result | Notes / Artifact |
|---|---|---|---|
| Smoke | `powershell -File tests\testFabricSkills.ps1 ...` | PASS / FAIL / N/A | name the smoke test |
| Individual eval | `tests/full-eval-tests/plan/03-individual-skills/eval-*.md` | PASS / FAIL / N/A | name the plan used |
| Combined eval | `tests/full-eval-tests/plan/04-combined-skills/...` | PASS / FAIL / N/A | if applicable |
| Other manual validation | `<command or workflow>` | PASS / FAIL / N/A | optional |
```

For a **new skill** or a **material skill behavior change**, add these manual results to
the PR when they apply:

1. If smoke coverage is present or updated, run the smoke harness:

```powershell
powershell -File tests\testFabricSkills.ps1 -testName "<smoke-test-name>" -directoryPath C:\temp\fabric-smoke
```

2. If the PR adds a new skill or materially changes skill behavior, record individual-eval
   results aligned to the relevant `tests/full-eval-tests/plan/03-individual-skills/eval-*.md` plan.
3. If the PR changes a paired or handoff workflow, record combined-eval results too.

Notes:

- `tests/coverage_gap_report.py` is an **asset audit**, not a behavior test. It confirms whether the repo sees your skill as missing smoke / eval assets.
- `tests/coverage_enforcement.py` is the **blocking policy check** for new-skill ownership / smoke / eval requirements.
- `tests/run-full-tests.ps1` is the current **full eval suite runner**. If you use it, record the relevant per-skill result plus the merged summary in the `Validation Results` section. If you validate manually against the individual eval plan instead, record the prompt steps and outputs there.
- For manual smoke or eval runs, name the exact smoke test or eval plan you used. Logs and pasted output are preferred; screenshots are optional supporting artifacts.

### Fixing Common Issues

| Issue | Fix |
|-------|-----|
| Missing frontmatter | Add `---` delimited YAML at file start with `name:` and `description:` |
| Missing update notice | Add the blockquote from CONTRIBUTING.md template |
| Broken reference | Fix relative path or update referenced file location |
| Untagged code block | Add language after opening ``` (e.g., ```bash) |
| Semantic conflict | Differentiate description from conflicting skill |

## Maintaining the Changelog

When adding or modifying skills, update `CHANGELOG.md` at the repository root:

1. Add your changes under the `[Unreleased]` section
2. Use these categories:
   - **Added** - New skills or features
   - **Changed** - Changes to existing skills
   - **Fixed** - Bug fixes
   - **Removed** - Removed skills or features
3. Keep entries concise and user-focused

Example:
```markdown
## [Unreleased]

### Added
- New `realtime-dev` skill for Real-Time Intelligence workloads

### Changed
- Updated `warehouse-dev` with new COPY INTO examples
```

When a release is made, maintainers will move `[Unreleased]` entries to a versioned section.

## Creating a Release (Maintainers)

To create a full release (catalog update, version stamp, tag, and GitHub release), run:

```powershell
# Preview changes locally (no commit/push)
.\ReleaseScripts\CreateFullRelease.ps1

# Full release: commit, tag, push, and create GitHub Release
.\ReleaseScripts\CreateFullRelease.ps1 --commit-and-push
```

This interactive script will:
1. Regenerate the skill catalog from `skills/*/SKILL.md` frontmatter
2. Show the 3 most recent version tags and suggest the next patch version
3. Stamp the version in `package.json`, `marketplace.json`, and related files
4. Commit, tag, push, and create a GitHub Release

**Prerequisites:** `git`, `python`, and `gh` (GitHub CLI) must be installed and in PATH.

## Generating Changelog (Maintainers)

Use the changelog generator to create release notes from merged PRs:

```bash
# Preview changes since last release
python .github/scripts/generate_changelog.py

# Update [Unreleased] section with PR summaries
python .github/scripts/generate_changelog.py --update

# Finalize a release (creates versioned section)
python .github/scripts/generate_changelog.py --release 0.2.0
```

For best results, set `GITHUB_TOKEN` to fetch PR titles and labels:
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

The generator categorizes PRs by title prefix or labels:
- `feat:`, `add:`, `new:` → **Added**
- `fix:`, `bug:` → **Fixed**
- `docs:` → **Documentation**
- `refactor:`, `update:` → **Changed**

## Documentation

For detailed contributor guides:

| Guide | Purpose |
|-------|---------|
| [Architecture Overview](docs/architecture-overview.md) | Repository structure |
| [Skill Authoring Guide](docs/skill-authoring-guide.md) | Create skills (comprehensive) |
| [Common Folder Guide](docs/common-folder-guide.md) | Shared reference docs |
| [Plugins Guide](docs/plugins-guide.md) | Skill bundling |
| [Quality Requirements](docs/quality-requirements.md) | Quality standards |
| [Testing Guide](docs/testing-guide.md) | Tests and CI/CD |
| [MCP Servers Guide](docs/mcp-servers-guide.md) | MCP registration |
| [Skill Catalog](docs/skill-catalog.md) | Existing skills |

For planning documents (ADRs, specs, RFCs): see [docs/README.md](docs/README.md)

## Questions?

Open an issue or ask in discussions!
