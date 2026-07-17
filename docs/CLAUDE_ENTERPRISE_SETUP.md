# Claude Code Enterprise Setup for Hermes and XCore

This repository already contains a broad MCP inventory. The curated HELIOS project overlay is stored at `config/claude/helios-enterprise-mcp.json` so existing local MCP configuration is not overwritten.

## Setup

```powershell
npm install -g @anthropic-ai/claude-code
claude doctor
```

Review `CLAUDE.md` and the curated overlay, then add only the required project servers to Claude Code. Keep the default permission mode at planning/read-only until the linked GitHub issue and approval gate authorize a write.

## Curated services

- Azure MCP Server
- Azure DevOps MCP Server
- GitHub MCP Server
- Linear MCP Server
- Microsoft Foundry MCP Server

## Boundaries

Claude Code may implement and test adapters, generate PRs, and summarize evidence. It may not grant Azure or Microsoft permissions, expose credentials, publish private memory, deploy production, merge promotion PRs, or bypass the canonical HELIOS control plane.
