# Hermes/XCore Claude Code Instructions

This repository is the bounded fleet-adapter companion to `M0nado/helios-platform`.

## Responsibilities

- Hermes and XCore worker registration
- routing and evaluation adapters
- redacted task and memory contracts
- local Docker, WSL2, and Hyper-V topology validation
- provider-neutral execution evidence for Claude Code, OpenAI, Microsoft Copilot, Foundry, and HELIOS

## Boundaries

- GitHub Issue `M0nado/helios-platform#165` owns the enterprise fleet contract.
- GitHub Issue `M0nado/helios-platform#162` blocks production enablement.
- This repository does not create Azure identities, grant RBAC, approve Graph permissions, write secrets, merge enterprise promotion pull requests, or deploy production resources.
- Claude Code defaults to planning and reviewed code changes. Permission-skipping modes are prohibited.
- Raw private AIHub or XCore memory must never be published to GitHub, Slack, Teams, Linear, SharePoint, traces, or prompts.

## Workflow

1. Start from the linked platform or fleet issue.
2. Keep adapters aligned with the canonical registries in `M0nado/helios-platform`.
3. Add tests for every allowed and denied capability.
4. Emit correlation IDs and evidence links.
5. Open a pull request and preserve rollback notes.
