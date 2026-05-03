# Changelog

All notable changes to the skills-for-fabric marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Renamed `sqldw-monitoring-cli` → `sqldw-operations-cli`** to align with the three-category governance (`-authoring-`, `-consumption-`, `-operations-`). Folder, SKILL.md `name:`, ownership manifest, agents, README, docs, compatibility files, and tests updated.
- **Manifest-driven plugin builds (Stage 2 — partial)** — plugins are now declared via `plugins/<name>/plugin.json` manifests listing the skills, agents, and MCP servers each plugin includes. The materialized plugin trees (`plugins/<name>/{skills,agents,common,.mcp.json}`) are produced by `build/build_plugins.py` from the canonical `skills/`, `agents/`, `common/` sources and are gitignored — only the manifest is checked in. The `common/*.md` closure is auto-derived by parsing `../../common/X.md` references inside each included skill, so `common/` files no longer need to be hand-mirrored per plugin. CI workflow and marketplace generation deferred to a follow-up.
- **Plugin installation granularity (Stage 1)** — each plugin now ships from its own self-contained source directory under `plugins/<name>/`, instead of all plugins sharing `"source": "./"`. Installing `fabric-authoring` no longer copies consumption skills (and vice versa). Internal repo files (`tests/`, `docs/`, `compatibility/`, `ReleaseScripts/`, dev configs) are no longer shipped to users.
- Each plugin now carries its own `.mcp.json` scoped to the MCP servers it actually needs (`fabric-authoring` and `fabric-operations` are empty; `fabric-consumption` and `fabric-skills` keep `PowerBIQuery`).
- Both `.claude-plugin/marketplace.json` and `.github/plugin/marketplace.json` updated to the new per-plugin `source` paths and remain byte-identical.
- Version bumped to `0.3.0` to reflect the distribution change.
- Updated `common/COMMON-CLI.md` — Added Catalog Search API as item discovery method alongside existing list-and-filter pattern
- Updated `common/COMMON-CORE.md` — Added Catalog Search API spec and cross-workspace item resolution

### Added
- New `fabric-operations` plugin — bundles `sqldw-operations-cli` (and `check-updates`) for users who only need diagnostics and performance investigation skills.
- `powerbi-authoring-cli` is now declared in `fabric-authoring` and `fabric-skills` (previously only existed canonically in `skills/`).
- `sqldw-operations-cli` is also included in the `fabric-skills` mega-bundle.
- New `skills/search-consumption-cli/` — Search the OneLake catalog to find Fabric items by name, description, workspace name, or type via `az rest`
- New `.github/skill-ownership.yml` manifest for repo ownership buckets across checked-in skills
- New `docs/contributor-kit.md` contributor guide for ownership and coverage expectations
- New `tests/test_skill_ownership_manifest.py` validation for keeping the ownership manifest in sync with checked-in skills
- New `skills/spark-diagnostics-cli/` — Diagnostic skill for Spark job failure triage, Livy session health monitoring, and performance bottleneck analysis using Fabric REST APIs and GA Spark Monitoring APIs
- New `common/SPARK-MONITORING-CORE.md` — Shared reference for GA Fabric Spark Monitoring APIs (Spark Advisor, Resource Usage, History Server, Driver/Executor Logs) used by all Spark skills
- Updated `agents/FabricDataEngineer.agent.md` with `spark-diagnostics-cli` delegation
- Updated compatibility files (AGENTS.md, CLAUDE.md, .cursorrules, .windsurfrules) with diagnostic skill references
- New `skills/synapse-migration/` — Migration skill for Azure Synapse Analytics → Microsoft Fabric. Covers `mssparkutils` → `notebookutils` API mapping, Linked Services → Data Connections/OneLake Shortcuts, Dedicated SQL Pool → Fabric Warehouse (T-SQL gaps, COPY INTO), Synapse Pipelines → Fabric Pipelines, and Spark pool configuration differences.
- New `skills/hdinsight-migration/` — Migration skill for Azure HDInsight → Microsoft Fabric. Covers `HiveContext`/`SparkContext` → `SparkSession`, WASB/ABFS → OneLake path conversion, Hive DDL → Delta Lake / Lakehouse schemas, Oozie → Fabric Pipelines, and introducing `notebookutils` as net-new capability.
- New `skills/databricks-migration/` — Migration skill for Databricks → Microsoft Fabric. Covers exhaustive `dbutils` → `notebookutils` API mapping (`fs`, `secrets`, `notebook`), widget → parameter cell replacement, `dbutils.library` → Fabric Environments, Unity Catalog → Lakehouse schema migration, Databricks Jobs → SJD, MLflow → Fabric ML Experiments, and Delta Sharing → OneLake Shortcuts.
- New `agents/FabricMigrationEngineer.agent.md` — Migration orchestration agent for cross-platform workload migrations (Synapse/HDInsight/Databricks → Fabric). Defines 6-phase migration framework (Assessment → Architecture Mapping → Environment Setup → Code Migration → Validation → Cutover) and delegates to migration skills + authoring skills.
- Updated `agents/FabricDataEngineer.agent.md` with delegation to `FabricMigrationEngineer` for all workload migration requests.

- New `skills/eventhouse-consumption-cli/` — Read-only KQL queries against Fabric Eventhouse and KQL Databases via `az rest`
- New `skills/eventhouse-authoring-cli/` — KQL management commands (table management, ingestion, policies, materialized views, functions) via `az rest`
- New `common/EVENTHOUSE-CONSUMPTION-CORE.md` — KQL query patterns, operators, data types, performance best practices
- New `common/EVENTHOUSE-AUTHORING-CORE.md` — KQL management command reference, policies, ingestion patterns, schema evolution
- Updated `agents/FabricDataEngineer.agent.md` with KQL skill delegation
- Updated compatibility files (AGENTS.md, CLAUDE.md, .cursorrules, .windsurfrules) with KQL patterns and skill references
- New `agents/FabricDataEngineer.agent.md` data engineering orchestration agent for medallion resource guidance.
- New `agents/FabricAdmin.agent.md` administration orchestration agent for capacity, governance, cost optimization, and workspace documentation.
- New `agents/FabricAppDev.agent.md` application developer agents, for building applications connected to Fabric
- **Consumer Skills**: `powerbi-consumption-cli`
- **spark-authoring-cli**: New `resources/notebook-api-operations.md` resource — step-by-step CLI guide for reading and updating Fabric notebook content via REST API. Covers: `getDefinition`/`updateDefinition` full LRO flow, base64 encode/decode patterns, cell modification examples, and an end-to-end script.
- **spark-authoring-cli** SKILL.md: Added 9 new TOC entries pointing to `notebook-api-operations.md` sections.
- **SPARK-AUTHORING-CORE.md**: Added 4 new gotchas (#11–#14): HTTP 411 empty body, HTTP 400 `updateMetadata` flag, `getDefinition` `/result` suffix, and source line `\n` requirement. Added `getDefinition` read pattern to Quick Reference decision guide.
- Hybrid architecture documentation updates describing Agents → Skills → Common layering and the skill-vs-agent decision framework.
- New `skills/dataflows-authoring-cli/` — Create, update, and manage Fabric Dataflows Gen2 artifacts and Power Query M mashup definitions via CLI
- New `skills/dataflows-consumption-cli/` — Explore, monitor, and query Fabric Dataflows Gen2 artifacts via CLI
- New `common/DATAFLOWS-AUTHORING-CORE.md` — Dataflows Gen2 authoring patterns, REST API surface, definition structure, M code, connections, ALM
- New `common/DATAFLOWS-CONSUMPTION-CORE.md` — Dataflows Gen2 consumption patterns, monitoring, parameters, definition exploration
- New `skills/eventstream-authoring-cli/` — Create, configure, and deploy Fabric Eventstream real-time ingestion pipelines via CLI (20 source types, 7 operators, 4 destinations)
- New `skills/eventstream-consumption-cli/` — List, inspect, and monitor Fabric Eventstream pipelines and topologies via CLI
- New `common/EVENTSTREAM-AUTHORING-CORE.md` — Eventstream resource model, source/operator/destination catalogs, item definitions (base64 pattern), lifecycle APIs
- New `common/EVENTSTREAM-CONSUMPTION-CORE.md` — Eventstream discovery, topology inspection, health monitoring, validation checklists
- New `common/SPARK-NOTEBOOK-AUTHORING-CORE.md` — Shared Spark notebook authoring guidance: code generation approach, rules, module index with notebookutils API references
- New `common/notebook-authoring/` module folder — 9 modules (context resolution, lakehouse paths/tables, connections, library management, ML workflow, notebook resources, troubleshooting)
- New `docs/common-folder-guide.md` section documenting the module folder pattern for `common/`

### Changed
- Updated contributor and compatibility documentation to reflect agent-based orchestration in addition to skills.
- Updated `agents/FabricDataEngineer.agent.md` with Dataflows skill delegation
- Updated `agents/FabricAdmin.agent.md` with Dataflows skill delegation
- Updated `marketplace.json` plugin bundles with Dataflows skills
- Updated compatibility files (CLAUDE.md, .cursorrules, AGENTS.md, .windsurfrules) with Dataflows references
- Clarified the contributor validation workflow with explicit pre-merge commands, a structured `Validation Results` format for PRs, and guidance on when to use the coverage gap report versus the smoke / full-eval runners.
- Added blocking common-infra validation for shared auth/token guidance and shared `sqlcmd` setup guidance, plus encoding checks that now fail unreadable or mojibake-corrupted skill markdown files with matching semantic pytest coverage.
- Added enforced new-skill coverage policy via `.github/coverage-policy.yml`, a fast PR validation workflow with one sticky summary comment, required `Validation Results` gating for skill PRs, skill-catalog sync checks, and security-report artifact fixes that remove noisy PR comments.
- **spark-authoring-cli**: Added notebook cell code authoring capabilities (PySpark, Scala, SparkR, SQL) with new triggers and Rule 4 for notebook authoring
- Updated `agents/FabricDataEngineer.agent.md` with notebook code authoring delegation to `spark-authoring-cli`

## [0.1.6] - 2026-02-10

### Added
- Skills compatibility test for validating skill routing and disambiguation

### Changed
- Updated plugins to version 0.1.6

## [0.1.5] - 2026-02-09

### Added
- Functional tests for the project
- Skill routing tests replacing Fabric integration tests
- Check for updates in Spark consumption skill

### Changed
- Renamed data-engineering skills to Spark
- Refactored the plugins
- Stricter semantic similarity thresholds (30% error, 20% warning)
- Optimized skills with API parameterization and token reduction
- Updated quality check for content review

### Fixed
- Updated .gitignore to exclude pycache files
- Encoding issues and duplicate triggers
- Livy endpoints with versioned paths and MSIT authentication

## [0.1.4] - 2026-02-08
### Added
- Feature/data analyst odbc (#5)
- Fabric Data Agent skills (dev and eval) (#2)

### Changed
- Enhance Data Engineering Skills: Session Management & Notebook Execution (#8)
- Merge branch 'master' of https://github.com/microsoft/skills-for-fabric
- Rename skill to spark-sql-odbc (#7)
- Fabric Data Engineering Skills  + Comprehensive Security Infrastructure (#3)

### Fixed
- Repo path in README (#6)

## [0.1.3] - 2026-02-07

### Added
- Fixed update command

## [0.1.2] - 2026-02-07

### Added
- Automatic plugin updates

## [0.1.0] - 2026-02-04

### Added
- Initial release of Microsoft Fabric Skills marketplace
- **Developer Skills**: `sqldw-authoring-cli`
- **Consumer Skills**: `sqldw-consumption-cli`
- **End-to-End Skills**: tbd
- **Update Checking**: Automatic update notifications at session start
- Cross-tool compatibility (GitHub Copilot CLI, VS Code, Claude Code, Cursor, Windsurf, Codex/Jules)
- Installation scripts for Windows (`install.ps1`) and Unix (`install.sh`)
- MCP server registration scripts

[Unreleased]: https://github.com/microsoft/skills-for-fabric/compare/v0.1.6...HEAD
[0.1.6]: https://github.com/microsoft/skills-for-fabric/compare/v0.1.5...v0.1.6
[0.1.5]: https://github.com/microsoft/skills-for-fabric/compare/v0.1.4...v0.1.5
[0.1.4]: https://github.com/microsoft/skills-for-fabric/compare/v0.1.0...v0.1.4
[0.1.3]: https://github.com/microsoft/skills-for-fabric/compare/v0.1.0...v0.1.3
[0.1.2]: https://github.com/microsoft/skills-for-fabric/compare/v0.1.0...v0.1.2
[0.1.0]: https://github.com/microsoft/skills-for-fabric/releases/tag/v0.1.0
