# GitHub Project Custom Fields Documentation
**Complete Reference** | **20+ Field Definitions**

---

## Table of Contents
1. [Field Types](#field-types)
2. [Core Phase & Planning Fields](#core-phase--planning-fields)
3. [Execution & Tracking Fields](#execution--tracking-fields)
4. [Resource & Assignment Fields](#resource--assignment-fields)
5. [Metrics & Health Fields](#metrics--health-fields)
6. [Additional Strategic Fields](#additional-strategic-fields)
7. [Field Usage Guide](#field-usage-guide)
8. [Quick Reference](#quick-reference)

---

## Field Types

### Available Field Types in GitHub Projects

| Type | Description | Use Cases |
|------|-------------|-----------|
| **Single Select** | Choose one from predefined options | Phase, Priority, Status |
| **Multiple Select** | Choose multiple from predefined options | Labels, tags, categories |
| **Number** | Numeric value (int/float) | Effort, coverage, days |
| **Date** | Calendar date selection | Due date, start date |
| **Text** | Free-form text input | Notes, descriptions, identifiers |
| **Checkbox** | True/False toggle | Feature flags, completeness |
| **Iteration** | Sprint or cycle selection | Sprint, release cycle |

---

## Core Phase & Planning Fields

### 1. Phase
**Type**: Single Select  
**Purpose**: Categorize work by deployment phase  
**Options**:
- Phase 0 - Preflight Checks
- Phase 1 - Infrastructure Setup
- Phase 2 - Agent Fleet Deployment
- Phase 3 - AI Services Integration
- Phase 4 - Security Hardening
- Phase 5 - Monitoring & Observability
- Phase 6 - Verification & Go-Live

**Color Coding**:
- Phase 0: Gray (neutral)
- Phase 1: Blue (infrastructure)
- Phase 2: Purple (deployment)
- Phase 3: Green (services)
- Phase 4: Red (security)
- Phase 5: Orange (operations)
- Phase 6: Gold (launch)

**Usage**: Filter by phase in views, group by phase in dashboards

---

### 2. Priority
**Type**: Single Select  
**Purpose**: Indicate work urgency and importance  
**Options**:
- 🔴 Critical (P0) - Blocks other work, must complete
- 🟠 High (P1) - Important, should complete soon
- 🟡 Medium (P2) - Normal priority, plan for later
- 🔵 Low (P3) - Nice to have, can defer

**Color Coding**:
- Critical: Red (#FF0000)
- High: Orange (#FF6600)
- Medium: Yellow (#FFCC00)
- Low: Blue (#0066CC)

**Usage**: Sort by priority, set alert on critical, schedule high priority first

---

### 3. Component
**Type**: Single Select  
**Purpose**: Identify which system/service the work affects  
**Options**:
- Infrastructure - K8s, networking, storage
- Agent-Fleet - Agent orchestration, deployment
- AI-Services - Model serving, inference APIs
- Security - Auth, encryption, compliance
- Monitoring - Observability, alerting, dashboards
- DevOps - CI/CD, deployment automation
- Documentation - Docs, guides, training

**Usage**: Group by component, filter for component leads, track component progress

---

### 4. Sprint
**Type**: Single Select  
**Purpose**: Assign work to sprint/iteration cycles  
**Options**:
- Sprint 1
- Sprint 2
- Sprint 3
- Sprint 4
- Sprint 5
- Sprint 6
- Backlog (no sprint)

**Duration**: Typically 2-week sprints  
**Usage**: Track sprint velocity, plan capacity, organize standups

---

### 5. Milestone
**Type**: Single Select  
**Purpose**: Group work by major release milestones  
**Options**:
- Foundation - Phase 1 infrastructure
- Deployment - Phase 2 agent fleet
- Enhancement - Phases 3-4 integration
- Completion - Phases 5-6 operations

**Usage**: Track milestone progress, link to release planning

---

## Execution & Tracking Fields

### 6. Estimated Effort
**Type**: Single Select  
**Purpose**: Story points for sprint planning  
**Options**:
- 1 - Trivial task
- 2 - Simple task
- 3 - Straightforward task
- 5 - Medium complexity
- 8 - High complexity
- 13 - Very high complexity
- 21 - Epic-level task

**Scale**: Modified Fibonacci for velocity estimation  
**Usage**: Sprint planning, capacity allocation, velocity tracking

---

### 7. Actual Effort
**Type**: Number  
**Purpose**: Track actual time/effort spent  
**Unit**: Hours or days (use consistently)  
**Range**: 0-1000  
**Usage**: Compare estimate vs. actual, improve estimation accuracy

---

### 8. Status Detail
**Type**: Single Select  
**Purpose**: Fine-grained work status (complements column position)  
**Options**:
- Backlog - Not yet prioritized
- Ready - Ready to start (all dependencies met)
- In Development - Active coding/implementation
- Code Review - PR submitted, awaiting review
- Testing - In QA or integration test
- Blocked - Cannot proceed (dependency issue)
- Complete - Finished and merged

**Usage**: Override column for more detail, track blockers, identify waiting time

---

### 9. Risk Level
**Type**: Single Select  
**Purpose**: Identify work with elevated risk  
**Options**:
- 🟢 Low - Straightforward, proven approach
- 🟡 Medium - Some unknowns, mitigatable
- 🟠 High - Significant unknowns, complex
- 🔴 Critical - Blocking, high failure risk

**Color Coding**:
- Low: Green (#00CC00)
- Medium: Yellow (#FFCC00)
- High: Orange (#FF6600)
- Critical: Red (#FF0000)

**Usage**: Risk dashboard, escalation tracking, resource allocation

---

### 10. Dependency Chain
**Type**: Text  
**Purpose**: Document issue dependencies as text  
**Format**: Comma-separated issue numbers or descriptions  
**Example**: `Depends on: #145, #146 | Blocks: #150`  
**Usage**: Manual dependency tracking, identify critical paths

---

## Resource & Assignment Fields

### 11. Assigned Team
**Type**: Single Select  
**Purpose**: Track which team owns the work  
**Options**:
- Backend
- Frontend
- DevOps
- QA / Testing
- Security
- Infrastructure
- Data / Analytics
- Documentation

**Usage**: Group by team, track team workload, schedule team standups

---

### 12. Code Owner
**Type**: Single Select  
**Purpose**: Primary code reviewer/owner  
**Options**: Team member names/handles  
**Usage**: Route PRs to correct owner, accountability tracking

---

### 13. Secondary Owner
**Type**: Single Select  
**Purpose**: Backup/secondary assignee  
**Options**: Team member names/handles  
**Usage**: Backup coverage, knowledge sharing, cross-training

---

### 14. Review Assigned To
**Type**: Single Select  
**Purpose**: Code reviewer assignment  
**Options**: Team member names/handles  
**Usage**: Route reviews, track review SLA, prevent bottlenecks

---

### 15. Stakeholder
**Type**: Single Select  
**Purpose**: Executive/PO stakeholder owner  
**Options**: Executive/leadership names  
**Usage**: Executive reporting, key initiative tracking

---

## Metrics & Health Fields

### 16. Test Coverage %
**Type**: Number  
**Purpose**: Code test coverage percentage  
**Range**: 0-100  
**Target**: 80%+ for production code  
**Usage**: Quality tracking, identify untested code

---

### 17. Deployment Target
**Type**: Single Select  
**Purpose**: Where the code will run  
**Options**:
- Staging - Test environment only
- Production - Live system
- Mixed - Multiple environments
- N/A - Not applicable (docs, docs, etc.)

**Usage**: Deployment planning, environment management

---

### 18. Health Status
**Type**: Single Select  
**Purpose**: Overall health of work item  
**Options**:
- 🟢 Healthy - On track, no issues
- 🟡 At-Risk - Some concerns, monitoring
- 🔴 Critical - Immediate intervention needed
- ❓ Unknown - Needs assessment

**Color Coding**:
- Healthy: Green
- At-Risk: Yellow
- Critical: Red
- Unknown: Gray

**Usage**: Executive dashboards, risk identification, escalation

---

### 19. Success Criteria Met
**Type**: Percentage (implement as 0-100 number field)  
**Purpose**: Percentage of acceptance criteria complete  
**Range**: 0-100%  
**Target**: 100% before done  
**Usage**: Track task completion, identify blockers to completion

---

### 20. Documentation
**Type**: Single Select  
**Purpose**: Documentation status  
**Options**:
- Complete - All docs written and reviewed
- Partial - Some docs complete, some pending
- Missing - No documentation yet
- In-Progress - Currently being written
- Not Required - No docs needed

**Usage**: Track documentation debt, ensure completeness

---

## Additional Strategic Fields

### 21. Architecture Impact
**Type**: Single Select  
**Purpose**: Scope of architectural implications  
**Options**:
- None - No architectural change
- Minor - Small localized change
- Major - Significant architectural change
- Breaking - Changes architectural patterns/interfaces

**Usage**: Architecture review, design decisions, long-term planning

---

### 22. Compliance Check
**Type**: Single Select  
**Purpose**: Compliance/audit status  
**Options**:
- Not Required - No compliance impact
- Pending - Awaiting compliance review
- Approved - Compliance team approved
- Failed - Does not meet compliance requirements

**Usage**: Compliance tracking, audit readiness, policy enforcement

---

### 23. Performance Impact
**Type**: Text  
**Purpose**: Description of performance implications  
**Format**: Brief description or metrics  
**Examples**: 
- "15% latency reduction"
- "10MB memory increase"
- "2x throughput improvement"

**Usage**: Performance tracking, capacity planning, optimization roadmap

---

### 24. Security Review Status
**Type**: Single Select  
**Purpose**: Security review and clearance  
**Options**:
- Not Required - No security impact
- Pending - Awaiting security review
- Approved - Security team approved
- Approved with Exceptions - Approved with noted exceptions
- Failed - Security review did not pass

**Usage**: Security gate, compliance tracking, vulnerability management

---

### 25. Integration Scope
**Type**: Single Select  
**Purpose**: Breadth of system integration  
**Options**:
- Isolated - Works independently
- Single Component - Integrates with one service
- Multi-Component - Integrates with 2-3 services
- System-Wide - Integrates with 4+ services

**Usage**: Complexity assessment, integration testing, rollout planning

---

## Field Usage Guide

### Creating Effective Fields

#### Field Naming Conventions
- **Use singular form**: "Status" not "Statuses"
- **Be specific**: "Risk Level" not "Risk"
- **Avoid jargon**: "Deployment Target" not "Env"
- **Descriptive**: "Code Coverage %" not just "Coverage"

#### Field Organization Best Practices

1. **Group Related Fields**: 
   - Core fields (Phase, Priority, Component)
   - Execution fields (Status, Effort, Health)
   - Resource fields (Assignee, Team, Owner)
   - Metrics fields (Coverage, Health, Impact)

2. **Consistent Color Coding**:
   - Red: Urgent, Critical, Risk
   - Yellow: Warning, Medium
   - Green: Good, Healthy, Low-risk
   - Blue: Information, Normal

3. **Option Naming**:
   - Use consistent emojis for status fields
   - Keep option names short (<20 chars)
   - Use leading numbers for ordering (e.g., "1-Low", "2-Medium")

### Recommended Field Templates

#### Minimal Setup (for small teams)
- Phase
- Priority
- Component
- Status Detail
- Assigned Team
- Health Status

#### Standard Setup (recommended)
- Add to minimal:
  - Sprint
  - Estimated Effort
  - Risk Level
  - Test Coverage %
  - Deployment Target

#### Advanced Setup (full featured)
- All standard fields plus:
  - Milestone
  - Code Owner
  - Actual Effort
  - Dependency Chain
  - Documentation
  - Architecture Impact
  - Compliance Check
  - Performance Impact

### Field Interdependencies

```
Phase
  ├─ Sprint (linked)
  ├─ Milestone (linked)
  └─ Risk Level (varies by phase)

Component
  ├─ Assigned Team (match component team)
  ├─ Code Owner (component owner)
  └─ Deployment Target (varies)

Priority
  ├─ Status Detail (urgent ≠ in progress)
  ├─ Risk Level (often correlated)
  └─ Health Status (high priority = monitor)

Status Detail
  ├─ Estimated Effort (ready = effort set)
  ├─ Dependency Chain (blocked = has dependencies)
  └─ Success Criteria Met (complete = 100%)
```

### Automation Using Fields

#### Auto-Populate Rules
```
When: Phase changes to "Phase 1"
Then: Set Component ← "Infrastructure" (if empty)
      Set Sprint ← "Sprint 1" (if empty)
```

#### Alert Rules
```
When: Health Status = "Critical"
And: Risk Level = "Critical"
Then: Assign to team lead
      Add label "escalate"
      Send notification
```

#### Report Rules
```
Group: Component
Count: By Status Detail
Aggregate: Sum of Actual Effort
Filter: Phase = "Phase 2"
```

---

## Quick Reference

### Fields by Category

**Planning** (5 fields)
- Phase, Priority, Component, Sprint, Milestone

**Execution** (5 fields)
- Estimated Effort, Actual Effort, Status Detail, Risk Level, Dependency Chain

**Resources** (5 fields)
- Assigned Team, Code Owner, Secondary Owner, Review Assigned To, Stakeholder

**Metrics** (5 fields)
- Test Coverage %, Deployment Target, Health Status, Success Criteria Met, Documentation

**Strategic** (5 fields)
- Architecture Impact, Compliance Check, Performance Impact, Security Review Status, Integration Scope

### Field Colors (Standard Scheme)

| Color | Use | Fields |
|-------|-----|--------|
| 🔴 Red | Critical, High priority, Urgent | Priority (Critical), Risk Level (Critical), Health (Critical) |
| 🟠 Orange | High priority, Elevated risk | Phase 5/6, Risk Level (High) |
| 🟡 Yellow | Medium, Warning, At-risk | Priority (Medium), Risk Level (Medium), Health (At-Risk) |
| 🟢 Green | Low priority, Healthy, Good | Priority (Low), Risk Level (Low), Health (Healthy) |
| 🔵 Blue | Information, Normal | Priority (Low), Phase 1/2 |
| ⚪ Gray | Neutral, Unknown, N/A | Unknown status, Phase 0 |
| 🟣 Purple | Deployment, Infrastructure | Phase 2, Infrastructure component |

### Typical Field Dependencies

```
Issue Created
  ├─ Phase ← Set immediately
  ├─ Component ← Set based on Phase
  ├─ Priority ← Set by PM
  └─ Status Detail ← "Backlog"

Issue Prioritized
  ├─ Priority ← Adjusted as needed
  ├─ Sprint ← Assigned if committed
  ├─ Estimated Effort ← Set during planning
  └─ Status Detail ← "Ready" (if dependencies met)

Issue Started
  ├─ Status Detail ← "In Development"
  ├─ Assigned Team ← Set
  └─ Health Status ← Monitor for "At-Risk"

Issue In Review
  ├─ Status Detail ← "Code Review"
  ├─ Review Assigned To ← Set
  └─ Test Coverage ← Ensure 80%+

Issue Complete
  ├─ Status Detail ← "Complete"
  ├─ Actual Effort ← Record hours spent
  ├─ Success Criteria Met ← 100%
  ├─ Health Status ← Final assessment
  └─ Documentation ← Verify complete
```

---

## Implementation Checklist

### Phase 1: Core Fields (1-5)
- [ ] Phase (mandatory)
- [ ] Priority (mandatory)
- [ ] Component (mandatory)
- [ ] Sprint (recommended)
- [ ] Milestone (recommended)

### Phase 2: Execution Fields (6-10)
- [ ] Estimated Effort
- [ ] Actual Effort
- [ ] Status Detail
- [ ] Risk Level
- [ ] Dependency Chain

### Phase 3: Resource Fields (11-15)
- [ ] Assigned Team
- [ ] Code Owner
- [ ] Secondary Owner
- [ ] Review Assigned To
- [ ] Stakeholder

### Phase 4: Metrics Fields (16-20)
- [ ] Test Coverage %
- [ ] Deployment Target
- [ ] Health Status
- [ ] Success Criteria Met
- [ ] Documentation

### Phase 5: Strategic Fields (21-25)
- [ ] Architecture Impact
- [ ] Compliance Check
- [ ] Performance Impact
- [ ] Security Review Status
- [ ] Integration Scope

---

**Last Updated**: 2024  
**Version**: 1.0  
**Maintained By**: Platform Team
