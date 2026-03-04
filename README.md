# Microsoft Fabric Skills

AI coding assistant skills for Microsoft Fabric developers and consumers. Optimized for GitHub Copilot CLI, with cross-compatibility for Claude Code, VS Code Copilot, Cursor, and other AI coding tools.


## How you can use Fabric Skills (CLI/Claude Code/VSCode prompts)
###  INTERNAL Microsoft -- a document with details is available here [Fabric SKills - Internal User Guide](https://microsoft-my.sharepoint.com/:w:/p/bocrivat/IQBxe55loRJmSa4S7vnDD_SUAWkvuTW7vwP4pd3k9FMGNek?e=My5R8c)


- **[Analytics PDF report](prompt_examples/NYC_AnalyzeExistingDataCreatePDF.txt)** — Analyzes Fabric data and produces a PDF report
- **[Document My Workspace](prompt_examples/DocumentMyWorkspace.txt)** — Analyzes Fabric data and produces a PDF report
- **[NYC Taxi - Fabric Medallion Project](prompt_examples/NYCTaxi_MedallionArchitecture.txt)** — Downloads a public dataset, prepares it in Spark and creates T-SQL 
views for consumption
- **[Dashboard App](prompt_examples/DashboardApp.txt)** — Generates an interactive dashboard which connects to Fabric data



## Installation

### GitHub Copilot CLI (Recommended)

**ALWAYS START WITH THIS: connect to the Fabric Skills Marketplace:**
```bash
/plugin marketplace add gim-home/FabricSkills
```

**Full bundle (all skills):**
```bash
/plugin install fabric-skills@fabric-skills-marketplace 
```

**Install by persona:**
```bash
# Developers only - SDKs, APIs, automation, CI/CD
/plugin install fabric-authoring@fabric-skills-marketplace 

# Consumers only - interactive queries, exploration, monitoring
/plugin install fabric-consumption@fabric-skills-marketplace 
```

**Filter by endpoint/engine (within any plugin):**
```bash
/plugin install fabric-skills@fabric-skills-marketplace  --filter "sqldw-*"
/plugin install fabric-skills@fabric-skills-marketplace  --filter "spark-*"
/plugin install fabric-skills@fabric-skills-marketplace  --filter "eventhouse-*"
```

### npm (Alternative) _ NOT YET TESTED

```bash
npm install -g @gim-home/fabric-skills
cd $(npm root -g)/@gim-home/fabric-skills

# Windows
.\install.ps1

# macOS/Linux
./install.sh
```

### Manual Installation

1. Clone this repository
2. Run the installer for your platform:
   - Windows: `.\install.ps1`
   - macOS/Linux: `./install.sh`




## Skills Overview

### Authentication

All Fabric operations require Azure AD authentication:

```bash
az login
az account get-access-token --resource https://api.fabric.microsoft.com
```


### Developer Skills (`-authoring-`)

For developers writing code - uses REST APIs for management, protocol-specific connections for data access.

| Skill | Pattern |
|-------|---------|
| `sqldw-authoring-cli` | Author Warehouses, Lakehouse SQL Endpoints, and Mirrored Databases from CLI environments |
| `spark-authoring-cli` | Develop Microsoft Fabric Spark/data engineering workflows with intelligent routing to specialized resources |
| `eventhouse-authoring-cli` | Execute KQL management commands (table management, ingestion, policies, materialized views, functions) against Fabric Eventhouse and KQL Databases via `az rest` |
| `powerbi-authoring-cli` | Create, manage, and deploy Power BI semantic models via `az rest` CLI against Fabric and Power BI REST APIs |

### Consumer Skills (`-consumption-`)

For interactive operations via MCP servers - no SDK/driver setup needed.

| Skill | Description |
|-------|-------------|
| `sqldw-consumption-cli` | Query Warehouses, Lakehouse SQL Endpoints, and Mirrored Databases from CLI environments |
| `spark-consumption-cli` | Query and analyze Microsoft Fabric Lakehouse tables  |
| `powerbi-consumption-cli` | Query semantic model metadata and run DAX against Power BI models |
| `eventhouse-consumption-cli` | Run read-only KQL queries against Fabric Eventhouse and KQL Databases via `az rest` |

### Utility Skills

| Skill | Description |
|-------|-------------|
| `check-updates` | Automatically checks for marketplace updates at session start |

### Agents

For cross-workload orchestration, FabricSkills now includes agent definitions:

| Agent | Purpose |
|-------|---------|
| `FabricDataEngineer` | Orchestrate medallion architecture, ETL/ELT, migration, and data quality workflows across Spark, SQL, and KQL skills |
| `FabricAdmin` | Manage capacity planning, governance, security, cost optimization, and observability across the Fabric tenant |

Agents and their resources live in `agents/`. See [Architecture Overview](docs/architecture-overview.md) for the skill-vs-agent decision framework.

## Automatic Update Checking

FabricSkills includes automatic update checking. At the start of each session, the first skill invoked will:

1. Check the [GitHub releases](https://github.com/gim-home/FabricSkills/releases) for the latest version
2. Compare against your installed version (from `package.json`)
3. If an update is available, display the changelog and provide update commands

This check runs **once per session** and is non-blocking—you can continue using skills even if you choose not to update.

To manually check for updates:
```bash
# GitHub Copilot CLI
/fabric-skills:check-updates
```

## Cross-Tool Compatibility

These skills work with multiple AI coding tools:

| Tool | Configuration |
|------|---------------|
| GitHub Copilot CLI | Automatic via plugin system |
| VS Code Copilot | Automatic via `.github/skills/` |
| Claude Code | Copy `compatibility/CLAUDE.md` to project root |
| Cursor | Copy `compatibility/.cursorrules` to project root |
| Codex/Jules | Copy `compatibility/AGENTS.md` to project root |
| Windsurf | Copy `compatibility/.windsurfrules` to project root |

The install scripts automate this setup.

## MCP Server Registration

If you have Fabric MCP servers (built separately), use the scripts in `mcp-setup/` to register them:

```bash
# Windows
.\mcp-setup\register-fabric-mcp.ps1

# macOS/Linux
./mcp-setup/register-fabric-mcp.sh
```

See [mcp-setup/README.md](mcp-setup/README.md) for details.

## Security & Responsible AI

### Security

FabricSkills implements focused security controls:

- ✅ **Secret Scanning**: TruffleHog + Gitleaks detect credentials
- ✅ **Prompt Injection Protection**: Automated scanning for dangerous patterns

**Report security vulnerabilities**: See [SECURITY.md](SECURITY.md)

**Optional Advanced Checks** (disabled by default, available as `.disabled` files):
- CodeQL SAST scanning
- Dependency review and Dependabot
- Python/Markdown/YAML linting
- CI test automation
- OpenSSF Scorecard

### Data Handling

- Skills process data locally or through authenticated Fabric APIs
- No data sent to third parties
- Credentials managed through Azure AD / GitHub Secrets
- Audit logging for tool executions


> **Note**: Use your Microsoft EMU GitHub account and do not include secrets or tokens in issue reports. For security vulnerabilities, report privately via [SECURITY.md](SECURITY.md).

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Development setup
- Security requirements
- Pull request process
- Coding standards

**Key requirements**:
- ✅ All tests pass
- ✅ Security scans pass
- ✅ Code owner approval
- ✅ No hardcoded secrets
- ✅ Prompt injection resistance

## Documentation

### For Users
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](SECURITY.md) - Security policy and reporting
- [SUPPORT.md](SUPPORT.md) - Getting help

### For Maintainers
- [docs/compliance/RAI_THREAT_MODEL.md](docs/compliance/RAI_THREAT_MODEL.md) - AI security threats and mitigations
- [docs/compliance/SECURITY_BASELINE.md](docs/compliance/SECURITY_BASELINE.md) - Supply chain security
- [docs/compliance/REPO_GUARDRAILS.md](docs/compliance/REPO_GUARDRAILS.md) - Repository configuration guide

### Reference
- [Fabric REST APIs](https://learn.microsoft.com/en-us/rest/api/fabric/articles/)
- [Microsoft Fabric Documentation](https://learn.microsoft.com/en-us/fabric/)

## License

MIT
