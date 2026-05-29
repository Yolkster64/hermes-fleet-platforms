# Security Guide

## Security Foundations
- C++/C# core for OS-level hardening, partition/memory/process isolation
- PowerShell only for controlled provisioning, never for persistent admin
- Vault and Quarantine as first-class concepts—always isolated and audit-logged
- All user/admin unlock actions require hardware token (USB) or local MFA

## Admin/Unlock Flow
- Sysadmin partition is always local-only, can’t be unlocked remotely
- Unlocking Vault or Quarantine always requires physical presence (local USB/Bio key)
- Firmware, driver, and network checks on every unlock; rollback if change detected

## Security Automation
- Embedded AI tracks processes, resources, threats, suspicious changes
- All AI code is reviewed and can’t escalate own privileges or exit sandboxes
- Data-leak prevention and file-watching (native, not just shell scripts)

## Audit/Logs
- Everything is logged, timestamped, signed
- Recovery and reporting tools in `/scripts` and `/tests`

See also: `/docs/GETTING_STARTED.md` and `/docs/PROFILES.md` on user/admin partitioning and scene switching.
