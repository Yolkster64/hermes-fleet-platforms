# GitHub Project Board Views Guide
**Complete Views Configuration** | **6 Custom Views**

---

## Table of Contents
1. [Views Overview](#views-overview)
2. [View 1: Timeline View](#view-1-timeline-view)
3. [View 2: Critical Path](#view-2-critical-path)
4. [View 3: Metrics Dashboard](#view-3-metrics-dashboard)
5. [View 4: Resource Planning](#view-4-resource-planning)
6. [View 5: Risk Analysis](#view-5-risk-analysis)
7. [View 6: Agent Status](#view-6-agent-status)
8. [Creating & Managing Views](#creating--managing-views)
9. [View Templates](#view-templates)

---

## Views Overview

### Why Multiple Views?

Different stakeholders need different perspectives:
- **Phase Leads**: Timeline/Phase view
- **Executives**: Critical Path/Risk
- **Tech Leads**: Metrics/Component
- **Team Members**: Resource/By Assignee
- **Operations**: Agent Status/Health

### Anatomy of a Project View

Each view consists of:

```
┌─ View Name
├─ Layout Type (Table, Board, Roadmap)
├─ Grouping Strategy
├─ Sorting Strategy
├─ Filtering Rules
├─ Visible Columns
├─ Aggregations
└─ Use Cases
```

### View Types Available

| Layout | Best For | Example |
|--------|----------|---------|
| **Table** | Detailed data, multi-dimensional | Timeline, Metrics, Resource |
| **Board** | Workflow, status progression | Critical Path (by status) |
| **Roadmap** | Timeline, phases over time | Phase timeline |

---

## View 1: Timeline View

### Purpose
Organize all work by deployment phase, showing complete phase structure with priority and timeline.

### Configuration

#### Layout
- **Type**: Table
- **Name**: "📅 Timeline View - By Phase"
- **Icon**: 📅

#### Grouping
- **Primary**: `Phase` (Phase 0 → Phase 6)
- **Secondary**: `Priority` (Critical → Low)
- **Direction**: Top to bottom

#### Sorting (within groups)
- **Sort 1**: `Milestone` (Foundation → Completion)
- **Sort 2**: `Priority` (Critical → Low)
- **Sort 3**: `Due Date` (earliest first)

#### Filtering
```
Show: All items
Hide: Archived items
Status Detail ≠ "Complete"
```

#### Visible Columns (in order)
1. **Title** (primary)
2. **Phase** (grouping indicator)
3. **Assignee**
4. **Due Date**
5. **Priority**
6. **Status Detail**
7. **Estimated Effort**
8. **Risk Level**
9. **Health Status**

#### Column Width Optimization
```
Title:            40%
Assignee:         10%
Due Date:         10%
Priority:         8%
Status Detail:    10%
Estimated Effort: 8%
Risk Level:       8%
Health Status:    6%
```

### Display Options
- **Grouping**: Enabled (by Phase)
- **Sorting**: Enabled
- **Filtering**: Enabled
- **Column Options**: Visible
- **Row Grouping**: Expandable

### Visual Enhancements
- **Color by Priority**: Red/Orange/Yellow/Blue
- **Color by Phase**: Phase-specific colors
- **Icons**: Priority indicators (🔴🟠🟡🔵)
- **Row Highlighting**: Current phase (bold)

### Usage Scenarios

#### For Phase Leads
```
"Show me all Phase 3 items organized by priority"
→ Filter: Phase = "Phase 3"
→ View: By Priority
→ Focus: High and Critical items first
```

#### For Executives
```
"What's the timeline for all critical items?"
→ Filter: Priority = "Critical"
→ View: Timeline View
→ Focus: Due dates and milestones
```

#### For Team Members
```
"What work do I have coming up?"
→ Filter: Assigned To = "Me"
→ View: Timeline View
→ Focus: Due dates and status
```

### Example View Output
```
Phase 0: Preflight Checks (4 items)
├─ [CRITICAL] Verify infrastructure readiness - Due: Jan 10
├─ [HIGH] Brief all teams - Due: Jan 11
├─ [MEDIUM] Review procedures - Due: Jan 12
└─ [LOW] Document architecture - Due: Jan 13

Phase 1: Infrastructure Setup (15 items)
├─ [CRITICAL] Deploy K8s cluster - Due: Jan 15
├─ [CRITICAL] Configure networking - Due: Jan 16
├─ [HIGH] Set up storage - Due: Jan 17
...
```

---

## View 2: Critical Path

### Purpose
Focus on critical and high-priority items that can block progress. Enable rapid response to blocking issues.

### Configuration

#### Layout
- **Type**: Board (Kanban-style)
- **Name**: "🚨 Critical Path - Priority Issues"
- **Icon**: 🚨

#### Board Columns
```
Backlog → Todo → In Progress → In Review → Done
```

#### Filtering
```
Priority = "Critical" OR Priority = "High"
Status Detail ≠ "Complete"
Archived = False
```

#### Grouping
- **Primary**: `Status Detail` (workflow progression)
- **Secondary**: `Component` (infrastructure, services, etc.)

#### Sorting (within groups)
- **Sort 1**: `Due Date` (earliest first)
- **Sort 2**: `Risk Level` (Critical → Low)
- **Sort 3**: `Health Status` (Critical → Healthy)

#### Visible Columns
1. **Title**
2. **Component**
3. **Assigned Team**
4. **Due Date**
5. **Estimated Effort**
6. **Risk Level**
7. **Health Status**
8. **Dependencies**

#### Column Limits (WIP)
```
Backlog:       No limit (growth phase)
Todo:          10 items max
In Progress:   8 items max
In Review:     6 items max
Done:          No limit
```

### Display Options
- **Grouping**: Enabled (by Status Detail)
- **Card Details**: Title, Component, Risk Level
- **Color Coding**: By Risk Level (Red/Orange/Yellow)
- **Icons**: Priority badges, status indicators

### Visual Enhancements
- **Card Color**: Red (Critical), Orange (High)
- **Badges**: Risk level, health status
- **Urgency Indicators**: Days until due (red if <3 days)
- **Row Highlighting**: Items nearing deadline

### Usage Scenarios

#### For Operations Team
```
"What critical items need attention right now?"
→ Filter: Critical OR High Priority
→ View: Critical Path
→ Focus: In Progress + In Review items
```

#### For Executive Standups
```
"Are we at risk of missing any critical milestones?"
→ Filter: Risk Level = "Critical"
→ View: Critical Path
→ Focus: Due dates and blockers
```

#### For Team Leads
```
"What critical work is blocking my team?"
→ Filter: Component = "My Component" AND Priority = "Critical"
→ View: Critical Path
→ Focus: Blockers and dependencies
```

### Example View Output
```
📋 Backlog (2 items)
├─ 🔴 [Critical] Upgrade security framework - Due: Jan 20
└─ 🔴 [Critical] Performance optimization - Due: Jan 22

📝 Todo (8 items)
├─ 🔴 [Critical] Deploy database changes - Due: Jan 15
├─ 🔴 [Critical] Configure load balancer - Due: Jan 16
├─ 🟠 [High] Update documentation - Due: Jan 17
...

🔄 In Progress (5 items)
├─ 🔴 [Critical] Fix security vulnerability - Due: Jan 12 (URGENT)
├─ 🔴 [Critical] Deploy agent fleet - Due: Jan 13
...

👀 In Review (4 items)
├─ 🔴 [Critical] Security hardening review - Due: Jan 14
...

✅ Done (0 items)
```

---

## View 3: Metrics Dashboard

### Purpose
Track health and progress by component, identify bottlenecks and component-level risks.

### Configuration

#### Layout
- **Type**: Table (aggregated data)
- **Name**: "📊 Metrics Dashboard - By Component"
- **Icon**: 📊

#### Grouping
- **Primary**: `Component` (all 7 components)
- **Secondary**: `Status Detail`

#### Sorting
- **Sort 1**: `Component` (Infrastructure → Documentation)
- **Sort 2**: `Health Status` (Critical → Healthy)

#### Filtering
```
Show: Active items
Hide: Archived items, Complete items
Status Detail ≠ "Complete"
```

#### Visible Columns
1. **Component** (group indicator)
2. **Count** (number of items)
3. **Status Detail** (breakdown)
4. **Test Coverage %** (aggregate)
5. **Average Effort**
6. **Health Status**
7. **Risk Level**
8. **On Track %**

#### Aggregation Rules
```
Count:
  ├─ By Component
  └─ By Status Detail

Average Effort (story points):
  ├─ Sum for each component
  └─ Items in progress

Test Coverage %:
  ├─ Average across component
  └─ Target: 80%+

Health Status:
  ├─ Most severe (Critical > At-Risk > Healthy)
  └─ Component overall health

On Track %:
  ├─ % of items meeting timeline
  └─ (Due Date >= Today) / Total
```

#### Calculations
```
Component Health Score = (Coverage % / 100) * (OnTrack % / 100) * 100

Example: Infrastructure
├─ Items: 8 (Backlog: 1, Todo: 2, In Progress: 3, In Review: 2)
├─ Coverage: 87%
├─ On Track: 100%
├─ Health Score: 87 (Very Good)
```

### Display Options
- **Metric Display**: Numbers + percentages
- **Color Coding**: By health status
- **Sparklines**: Trend data (if available)
- **Target Lines**: 80% coverage target

### Visual Enhancements
- **Component Icons**: Component-specific
- **Health Indicators**: 🟢🟡🔴
- **Target Markers**: 80% line for coverage
- **Trend Arrows**: ↑↓→

### Usage Scenarios

#### For Technical Leads
```
"How's each component doing?"
→ View: Metrics Dashboard
→ Focus: Health Status, Test Coverage %
```

#### For Product Managers
```
"What component is at risk?"
→ Filter: Health Status = "At-Risk" OR "Critical"
→ View: Metrics Dashboard
→ Focus: On Track %, Effort remaining
```

#### For QA Team
```
"Which components need more testing?"
→ Filter: Test Coverage % < 80%
→ View: Metrics Dashboard
→ Focus: Coverage %, Component
```

### Example View Output
```
📊 Component Summary

Component           Count  Backlog  Todo  In Prog  In Review  Coverage  OnTrack  Health
─────────────────────────────────────────────────────────────────────────────────────
Infrastructure      8      0        1     3        2          92%       100%     🟢
Agent-Fleet         6      1        2     2        1          87%       83%      🟡
AI-Services         10     2        3     3        2          78%       70%      🟡
Security            7      1        1     3        2          95%       100%     🟢
Monitoring          5      1        1     2        1          88%       100%     🟢
DevOps              4      0        2     1        1          85%       100%     🟢
Documentation       3      2        1     0        0          65%       50%      🔴

─────────────────────────────────────────────────────────────────────────────────────
Total               43     7        11    14       9          85%       86%      🟡
```

---

## View 4: Resource Planning

### Purpose
Track work by team and assignee, identify overload, enable capacity planning.

### Configuration

#### Layout
- **Type**: Table
- **Name**: "👥 Resource Planning - By Assignee"
- **Icon**: 👥

#### Grouping
- **Primary**: `Assigned Team` (Backend, Frontend, DevOps, QA, Security, Infra, Docs)
- **Secondary**: `Assignee` (individual team member)

#### Sorting (within groups)
- **Sort 1**: `Estimated Effort` (high to low)
- **Sort 2**: `Due Date` (earliest first)
- **Sort 3**: `Priority` (Critical → Low)

#### Filtering
```
Status Detail = "Ready" OR "In Development" OR "Code Review"
Assigned Team ≠ Unassigned
```

#### Visible Columns
1. **Team** (grouping)
2. **Assignee** (secondary grouping)
3. **Title**
4. **Component**
5. **Estimated Effort**
6. **Actual Effort**
7. **Due Date**
8. **Priority**
9. **Health Status**

#### Capacity Calculation
```
For each assignee:
  ├─ Total Effort (sum of Estimated Effort for active items)
  ├─ Sprint Capacity (assume 40 hours/week)
  ├─ Utilization %
  └─ Available Capacity (40 - Total) hours
```

### Display Options
- **Show Capacity**: Utilization % and capacity bar
- **Highlight Overload**: > 100% capacity
- **Sort Options**: By effort, by due date
- **Filter Options**: By team, by status

### Visual Enhancements
- **Capacity Bars**: Visual representation of workload
- **Overload Warning**: Red bars for >100%
- **On-Track Indicator**: 🟢🟡🔴
- **Effort Badges**: Points displayed

### Usage Scenarios

#### For Team Leads
```
"Is my team overloaded?"
→ Filter: Assigned Team = "My Team"
→ View: Resource Planning
→ Focus: Utilization %, overload detection
```

#### For HR/Capacity Planning
```
"Who has available capacity?"
→ Filter: Utilization % < 80%
→ View: Resource Planning
→ Focus: Available capacity, distribution
```

#### For Project Manager
```
"Can we fit this work in the sprint?"
→ View: Resource Planning
→ Focus: Available capacity by person
```

### Example View Output
```
👥 Resource Allocation Summary

Backend Team
├─ Alice Chen
│  ├─ [High] API Gateway Implementation - 13pts - Due: Jan 15
│  ├─ [Med] Database Optimization - 8pts - Due: Jan 18
│  └─ Utilization: 87% (35/40 hrs) - ✅ Healthy
├─ Bob Martinez
│  ├─ [Crit] Security Framework - 13pts - Due: Jan 12
│  ├─ [High] Logger Implementation - 5pts - Due: Jan 16
│  ├─ [High] Monitoring Integration - 8pts - Due: Jan 17
│  └─ Utilization: 108% (43/40 hrs) - ⚠️  OVERLOAD
└─ Team Capacity: 87/80 hrs (109%) - ⚠️  OVERLOADED

Frontend Team
├─ Carol Wilson
│  ├─ [Med] Dashboard Creation - 8pts - Due: Jan 20
│  └─ Utilization: 20% (8/40 hrs) - ✅ Available
├─ David Lee
│  ├─ [High] UI Components - 8pts - Due: Jan 17
│  └─ Utilization: 20% (8/40 hrs) - ✅ Available
└─ Team Capacity: 16/80 hrs (20%) - ✅ AVAILABLE
```

---

## View 5: Risk Analysis

### Purpose
Identify and track high-risk items, monitor risk indicators, enable proactive mitigation.

### Configuration

#### Layout
- **Type**: Table
- **Name**: "⚠️  Risk Analysis - Risk Assessment"
- **Icon**: ⚠️

#### Grouping
- **Primary**: `Risk Level` (Critical → Low)
- **Secondary**: `Health Status` (Critical → Healthy)

#### Sorting (within groups)
- **Sort 1**: `Priority` (Critical → Low)
- **Sort 2**: `Due Date` (earliest first)
- **Sort 3**: `Days Until Due` (latest first)

#### Filtering
```
Risk Level = "Medium" OR "High" OR "Critical"
Archived = False
```

#### Visible Columns
1. **Title**
2. **Risk Level**
3. **Health Status**
4. **Priority**
5. **Component**
6. **Assigned Team**
7. **Due Date**
8. **Days Until Due**
9. **Mitigation Notes**
10. **Escalation**

#### Risk Score Calculation
```
Risk Score = (Probability × Impact × Urgency) / 10

Where:
  - Probability: 1-3 (Low/Med/High)
  - Impact: 1-3 (Low/Med/High)
  - Urgency: Days until due / 30 (normalized)

Example:
  - High Probability (3) × High Impact (3) × 0.5 = 4.5/10
```

### Display Options
- **Color by Risk Level**: Red/Orange/Yellow
- **Sort by Risk Score**: Highest risk first
- **Show Mitigations**: Mitigation notes displayed
- **Highlight Urgent**: < 3 days to due date

### Visual Enhancements
- **Risk Badges**: 🔴🟠🟡 by risk level
- **Heat Map**: Color intensity by risk score
- **Trend Arrows**: Risk trajectory (↑↓→)
- **Escalation Flags**: ⚡ for items needing escalation

### Usage Scenarios

#### For Risk Manager
```
"What risks do we have?"
→ Filter: Risk Level ≠ Low
→ View: Risk Analysis
→ Focus: Mitigation notes, escalation
```

#### For Executive Leadership
```
"What could derail the deployment?"
→ Filter: Risk Level = "Critical"
→ View: Risk Analysis
→ Focus: Impact, mitigation strategies
```

#### For Team Leads
```
"What risks are on my team?"
→ Filter: Component = "My Component" AND Risk Level ≥ Medium
→ View: Risk Analysis
→ Focus: Mitigation, due dates
```

### Example View Output
```
⚠️  Risk Registry

🔴 Critical Risk (3 items)
├─ Issue #145: Database Migration Failure - Due: Jan 12 (2 days)
│  ├─ Probability: High | Impact: High | Overall: CRITICAL
│  ├─ Mitigation: Extensive testing, rollback plan ready
│  └─ Assigned: Bob Martinez
├─ Issue #156: Security Breach - Due: Jan 15 (5 days)
│  ├─ Probability: Medium | Impact: Critical | Overall: CRITICAL
│  ├─ Mitigation: Security hardening, pen test completed
│  └─ Assigned: Security Team
└─ Issue #167: Agent Deployment Failure - Due: Jan 18 (8 days)
   ├─ Probability: Medium | Impact: High | Overall: CRITICAL
   ├─ Mitigation: Staging validation, canary deployment
   └─ Assigned: DevOps Team

🟠 High Risk (7 items)
├─ Issue #123: Performance Regression - Due: Jan 20
├─ Issue #134: Integration Timeout - Due: Jan 17
...

🟡 Medium Risk (5 items)
├─ Issue #98: Documentation Gaps - Due: Jan 25
...
```

---

## View 6: Agent Status

### Purpose
Real-time operational monitoring of agent fleet deployment and component health for operations teams.

### Configuration

#### Layout
- **Type**: Table
- **Name**: "🤖 Agent Status - Operational View"
- **Icon**: 🤖

#### Grouping
- **Primary**: `Component` (Infrastructure, Agent-Fleet, AI-Services, etc.)
- **Secondary**: `Phase`

#### Sorting (within groups)
- **Sort 1**: `Health Status` (Critical → Healthy)
- **Sort 2**: `Status Detail` (workflow order)
- **Sort 3**: `Due Date` (earliest first)

#### Filtering
```
Component ∈ [Agent-Fleet, AI-Services, Infrastructure]
Deployment Target = "Production" OR "Staging"
Status Detail ≠ "Complete"
```

#### Visible Columns
1. **Component** (grouping)
2. **Phase**
3. **Title**
4. **Status Detail**
5. **Deployment Target**
6. **Health Status**
7. **Test Coverage %**
8. **Last Updated**
9. **Assigned Team**

#### Refresh Indicators
```
Last Updated: Automatic, shows time since last change
  - Green: < 1 hour
  - Yellow: 1-4 hours
  - Red: > 4 hours (stale)
```

### Display Options
- **Live Updates**: Real-time status refresh (5 sec)
- **Auto Refresh**: Enable for monitoring displays
- **Highlight Critical**: Red background for critical items
- **Show Timestamps**: Last updated time

### Visual Enhancements
- **Health Indicators**: 🟢🟡🔴 with status icon
- **Status Badges**: Current deployment status
- **Heartbeat Icon**: ❤️ for active items
- **Alert Badge**: ⚠️ for items needing attention

### Usage Scenarios

#### For Operations Center
```
"How is the production deployment going?"
→ Filter: Deployment Target = "Production"
→ View: Agent Status
→ Focus: Health Status, Last Updated
```

#### For SRE Team
```
"Is the agent fleet healthy?"
→ Filter: Component = "Agent-Fleet"
→ View: Agent Status
→ Focus: Health Status, Coverage, Incidents
```

#### For On-Call Engineer
```
"Any critical issues right now?"
→ Filter: Health Status = "Critical"
→ View: Agent Status
→ Focus: Component, Details, Assigned Team
```

### Example View Output
```
🤖 Operational Status Dashboard

Infrastructure (4 items) - Overall: 🟢 HEALTHY
├─ Phase 1: K8s Cluster Deploy
│  ├─ Status: In Progress
│  ├─ Health: 🟢 Healthy
│  ├─ Coverage: 92%
│  ├─ Last Updated: 5 min ago
│  └─ Team: Infrastructure
├─ Phase 1: Networking Setup
│  ├─ Status: In Review
│  ├─ Health: 🟢 Healthy
│  ├─ Coverage: 88%
│  ├─ Last Updated: 12 min ago
│  └─ Team: Infrastructure
...

Agent-Fleet (6 items) - Overall: 🟡 AT-RISK
├─ Phase 2: Agent Deployment
│  ├─ Status: In Progress
│  ├─ Health: 🟡 At-Risk
│  ├─ Coverage: 79% (⚠️  Below 80%)
│  ├─ Last Updated: 2 min ago
│  └─ Team: DevOps
├─ Phase 2: Agent Scaling
│  ├─ Status: In Progress
│  ├─ Health: 🟢 Healthy
│  ├─ Coverage: 85%
│  ├─ Last Updated: 8 min ago
│  └─ Team: DevOps
...

AI-Services (5 items) - Overall: 🟢 HEALTHY
├─ Phase 3: Model Deployment
│  ├─ Status: In Progress
│  ├─ Health: 🟢 Healthy
│  ├─ Coverage: 88%
│  ├─ Last Updated: 3 min ago
│  └─ Team: ML/AI
...
```

---

## Creating & Managing Views

### Step-by-Step: Create a New View

1. **Navigate to Project Board**
   - Go to your project board
   - Click **+ Add view** or **New view**

2. **Configure View Details**
   - **View Name**: Use emoji + descriptive name
   - **Layout**: Choose Table/Board/Roadmap
   - **Based On**: Select default view or start fresh

3. **Set Grouping**
   - **Primary Grouping**: Usually by Phase or Component
   - **Secondary Grouping**: Usually by Status or Priority
   - **Hide Empty Groups**: Optional

4. **Configure Sorting**
   - **Sort By**: Select primary sort field
   - **Then By**: Select secondary sort
   - **Direction**: Ascending/Descending

5. **Apply Filters**
   - **Add filters**: Narrow down items
   - Use AND/OR logic
   - Save filter combinations

6. **Select Visible Columns**
   - **Drag to reorder**: Most important first
   - **Resize columns**: Adjust width
   - **Hide columns**: Remove as needed

7. **Save View**
   - Click **Save**
   - View is now available to team

### View Naming Convention

```
[emoji] Action/Purpose - Key Detail

Examples:
- 📅 Timeline View - By Phase
- 🚨 Critical Path - Priority Issues
- 📊 Metrics Dashboard - By Component
- 👥 Resource Planning - By Assignee
- ⚠️  Risk Analysis - Risk Assessment
- 🤖 Agent Status - Operational View
```

### View Access & Sharing

```
Public: All team members can view
Private: Only creator can view
Shared: Specific people/teams
```

### Best Practices

1. **Keep Views Simple**
   - 6-10 columns maximum
   - 3-4 grouping levels maximum
   - Clear naming and purpose

2. **Use Consistent Emojis**
   - Same emoji for similar view types
   - Color coding by purpose
   - Intuitive at a glance

3. **Filter for Clarity**
   - Hide archived items
   - Hide completed items (unless reviewing)
   - Focus on actionable items

4. **Update Regularly**
   - Review views monthly
   - Adjust based on feedback
   - Remove unused views

---

## View Templates

### Quick Template Library

#### Template: Status Board
```yaml
Name: "[Status] {Component Name}"
Layout: Board
Grouping: Status Detail
Columns:
  - Title
  - Assignee
  - Due Date
  - Priority
```

#### Template: Phase View
```yaml
Name: "[Phase] {Phase Name}"
Layout: Table
Grouping: Status Detail
Filter: Phase = "{Phase}"
Columns:
  - Title
  - Component
  - Assignee
  - Effort
  - Health
```

#### Template: Team View
```yaml
Name: "[Team] {Team Name}"
Layout: Table
Grouping: Assignee
Filter: "Assigned Team = {Team}"
Columns:
  - Title
  - Effort
  - Due Date
  - Priority
  - Status
```

---

**Last Updated**: 2024  
**Version**: 1.0  
**Maintained By**: Platform Team
