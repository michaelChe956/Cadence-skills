---
name: status
description: Use when checking project progress, viewing phase status, calculating completion percentage, or displaying time statistics for Cadence workflows
---

# Status - View Project Progress

## Overview

**Core Principle**: Read project information from multiple sources, calculate progress percentage, and display formatted status overview.

The `status` skill provides a comprehensive view of your Cadence workflow progress by:
- Reading project information (CLAUDE.md, Git, Serena memory)
- Calculating overall progress (completed_phases / total_phases)
- Displaying time statistics
- Showing current phase status

## When to Use

**Use this skill when you need to:**
- Check current progress of a Cadence workflow
- See which phases are completed, in progress, or pending
- Calculate how much time has been spent
- Estimate remaining time
- Get a quick overview before resuming work

**Do NOT use for:**
- Real-time monitoring (use `/monitor` for snapshots)
- Creating checkpoints (use `/checkpoint` instead)
- Generating detailed reports (use `/report` instead)

## Data Sources

### Primary Data Source: Serena Memory

**Progress data structure:**
```yaml
memory_name: progress-{project_id}

metadata:
  version: "1.0"
  project_id: string
  project_name: string
  flow_type: "full-flow" | "quick-flow" | "exploration-flow"
  created_at: timestamp
  updated_at: timestamp

project_info:
  name: string
  current_phase: string
  git_branch: string

phases:
  - phase_name: string
    status: "completed" | "in_progress" | "pending"
    start_time: timestamp | null
    end_time: timestamp | null

overall_progress:
  percentage: number  # 0-100
  completed_phases: number
  total_phases: number

time_stats:
  total_time: number  # seconds
  estimated_remaining: number  # seconds
```

### Auxiliary Data Sources

1. **CLAUDE.md** - Project metadata
   - Project name
   - Project ID (if defined)
   - Project description

2. **Git** - Version control information
   - Current branch
   - Recent commits
   - Working directory status

3. **TodoWrite** - Current task states (optional)
   - Task status for current phase
   - Task dependencies

## The Process

### Step 1: Gather Project Information

**Read CLAUDE.md:**
```markdown
1. Read `.claude/CLAUDE.md` from project root
2. Extract:
   - Project name
   - Project ID (if defined, otherwise generate from directory name)
   - Project description
   - Tech stack (if relevant)
```

**Get Git information:**
```bash
# Get current branch
git branch --show-current

# Get recent commits (last 10)
git log --oneline -10

# Get working directory status
git status --short
```

**Read Serena memory:**
```markdown
1. List memories matching pattern: progress-*
2. Find the memory for current project: progress-{project_id}
3. Read the memory content
```

### Step 2: Read Progress Data

**Read Serena memory:**
```markdown
Call: mcp__serena__read_memory
Parameter: memory_name = "progress-{project_id}"

Expected data:
- metadata (version, project_id, flow_type)
- project_info (name, current_phase, git_branch)
- phases (list of phases with status and times)
- overall_progress (percentage, completed_phases, total_phases)
- time_stats (total_time, estimated_remaining)
```

### Step 2.5: Auto-Migrate and Validate (REQUIRED)

**🔴 CRITICAL: Auto-migrate old data and validate**

**Check version and migrate if needed:**
```markdown
Call: version-migration skill
Input: progress_data

IF version < current_version:
  → Auto-migrate to current version
  → Save migrated data
  → Log: "Progress migrated from v{old} to v{new}"
  → Use migrated data for display

IF version == current_version:
  → No migration needed
  → Continue with existing data
```

**Validate data format:**
```markdown
Call: data-validation skill
Input: progress_data

IF validation fails:
  → Log validation errors
  → Display warning to user
  → Show partial status (what's available)
  → DO NOT attempt to fix automatically

IF validation passes:
  → Continue to Step 3
```

**Why auto-migration and validation are REQUIRED:**
- Ensures data is always in current format
- Catches data corruption early
- Provides clear error messages
- Prevents cascading failures in other skills

### Step 3: Calculate Progress

**Calculate completion percentage:**
```python
# If overall_progress.percentage exists, use it
# Otherwise calculate from phases

completed_phases = sum(1 for phase in phases if phase.status == "completed")
total_phases = len(phases)
percentage = (completed_phases / total_phases) * 100

# Round to 1 decimal place
percentage = round(percentage, 1)
```

**Calculate time statistics:**
```python
# Calculate total time from phases
total_time = sum(
    (phase.end_time - phase.start_time)
    for phase in phases
    if phase.start_time and phase.end_time
)

# Estimate remaining time
if completed_phases > 0:
    avg_time_per_phase = total_time / completed_phases
    remaining_phases = total_phases - completed_phases
    estimated_remaining = avg_time_per_phase * remaining_phases
else:
    estimated_remaining = 0
```

**Format time for display:**
```python
def format_time(seconds):
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"
```

### Step 4: Format Output

**Header section:**
```markdown
📊 Project Progress: {project_name}

## Overall Progress
[{progress_bar}] {percentage}% ({completed_phases}/{total_phases} phases)

## Current Phase
**{current_phase_name}** - {status}
Started: {start_time} ({elapsed_time} ago)
```

**Progress bar generation:**
```python
def generate_progress_bar(percentage, width=12):
    filled = int(percentage / 100 * width)
    empty = width - filled
    return "█" * filled + "░" * empty
```

**Phase status section:**
```markdown
## Phase Status
✅ {phase_name} - Completed ({duration})
✅ {phase_name} - Completed ({duration})
✅ {phase_name} - Completed ({duration})
🔄 {phase_name} - In Progress ({elapsed_time})
⏳ {phase_name} - Pending
⏳ {phase_name} - Pending
⏳ {phase_name} - Pending
```

**Time statistics section:**
```markdown
## Time Statistics
Total Time: {total_time}
Estimated Remaining: {estimated_remaining}
```

**Git information section:**
```markdown
## Git Information
Branch: {branch_name}
Recent Commits: {commit_count}
```

**Next step section:**
```markdown
Next Step: {next_action}
```

### Step 5: Display Output

**Output the formatted status:**
```markdown
Print the complete formatted output to console.

Ensure:
- Clear visual hierarchy
- Consistent formatting
- Emoji usage for quick scanning
- Actionable next step at end
```

## Quick Reference

### Progress Calculation
| Metric | Formula | Notes |
|--------|--------|-------|
| Completion % | `(completed_phases / total_phases) * 100` | Rounded to 1 decimal |
| Total Time | `sum(end_time - start_time)` | Only for completed phases |
| Est. Remaining | `avg_time * remaining_phases` | Based on completed phases average |

### Data Source Priority
1. **Serena memory** (primary) - Progress data, phase status, time stats
2. **CLAUDE.md** (auxiliary) - Project metadata
3. **Git** (auxiliary) - Branch info, commits
4. **TodoWrite** (optional) - Current task states

### Phase Status Mapping
| Status | Symbol | Meaning |
|--------|-------|---------|
| `completed` | ✅ | Phase finished, end_time set |
| `in_progress` | 🔄 | Phase started, currently running |
| `pending` | ⏳ | Phase not started yet |

## Code Example

### Reading Progress Data

```python
# Step 1: Get project ID
project_id = get_project_id_from_claude_md()  # or directory name

# Step 2: Read Serena memory
memory_name = f"progress-{project_id}"
progress_data = mcp__serena__read_memory(memory_name)

# Step 3: Validate data
if not progress_data:
    print("No progress data found. Start a workflow first.")
    return

# Step 4: Calculate progress
completed = sum(1 for p in progress_data.phases if p.status == "completed")
total = len(progress_data.phases)
percentage = round((completed / total) * 100, 1)

# Step 5: Format and display
print(f"📊 Progress: {percentage}% ({completed}/{total} phases)")
```

### Calculating Time Statistics

```python
from datetime import datetime

# Calculate total time for completed phases
total_seconds = 0
for phase in progress_data.phases:
    if phase.status == "completed" and phase.start_time and phase.end_time:
        duration = phase.end_time - phase.start_time
        total_seconds += duration

# Calculate average time per phase
completed_count = sum(1 for p in progress_data.phases if p.status == "completed")
avg_time = total_seconds / completed_count if completed_count > 0 else 0

# Estimate remaining time
remaining_phases = total - completed_count
estimated_seconds = avg_time * remaining_phases

# Format for display
def format_duration(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return f"{int(seconds)}s"

print(f"Total: {format_duration(total_seconds)}")
print(f"Remaining: {format_duration(estimated_seconds)}")
```

## Common Mistakes

### ❌ Only Reading Git Commits
```python
# WRONG: Counting commits doesn't reflect phase completion
commits = get_git_commits()
progress = len(commits) / 10 * 100  # Incorrect!

# RIGHT: Read actual progress data from Serena
progress_data = read_serena_memory("progress-{project_id}")
progress = progress_data.overall_progress.percentage
```

### ❌ Ignoring Current Phase
```python
# WRONG: Not showing which phase is currently running
print(f"Progress: {percentage}%")

# RIGHT: Show current phase and status
print(f"Progress: {percentage}%")
print(f"Current Phase: {current_phase} - {status}")
```

### ❌ Missing Time Statistics
```python
# WRONG: Only showing percentage
print(f"Progress: 37.5%")

# RIGHT: Include time information
print(f"Progress: 37.5% (3/8 phases)")
print(f"Total Time: 5h")
print(f"Estimated Remaining: 8.3h")
```

### ❌ Poor Formatting
```python
# WRONG: Raw data dump
print(progress_data)

# RIGHT: Professional formatting with visual elements
print("📊 Project Progress: User Authentication System")
print("[████████░░░] 37.5% (3/8 phases)")
print("\n## Current Phase")
print("**Design** - In Progress")
```

## Red Flags

**Stop and investigate if:**
- ⚠️ **No progress data found** - Workflow may not have been started
- ⚠️ **Phase count mismatch** - total_phases doesn't match actual phases array length
- ⚠️ **Missing time data** - start_time or end_time missing for completed phases
- ⚠️ **Percentage seems wrong** - Verify calculation matches actual completed phases
- ⚠️ **Current phase not in list** - current_phase doesn't match any phase in phases array

**Common issues:**
- Progress data exists but phases array is empty
- Phase status is "in_progress" but start_time is null
- Phase status is "completed" but end_time is null
- Git branch doesn't match project_info.git_branch

## Integration Points

**This skill integrates with:**
- **Serena memory** - Primary data source for progress tracking
- **CLAUDE.md** - Project metadata source
- **Git commands** - Version control information
- **TodoWrite** - Optional task state source

**Related skills:**
- **Use `checkpoint`** - To save current progress state
- **Use `resume`** - To resume interrupted workflow
- **Use `report`** - To generate detailed progress report
- **Use `monitor`** - For status snapshot (same data, different display)

## Testing Checklist

Before deploying, verify:
- [ ] Reads progress data from Serena memory correctly
- [ ] calculates percentage correctly (completed_phases / total_phases)
- [ ] shows all phases with correct status symbols
- [ ] includes current phase information
- [ ] displays time statistics
- [ ] shows Git branch and commit count
- [ ] formats output professionally with visual elements
- [ ] provides actionable next step
- [ ] handles missing data gracefully (e.g., no progress found)
- [ ] validates data consistency (e.g., phase count matches)

## Deployment Notes

**Token efficiency:**
- Main content: ~400 tokens
- Code examples: ~300 tokens
- Quick reference: ~150 tokens
- **Total**: ~850 tokens (efficient for frequent use)

**Performance:**
- Read operations: 2-3 (CLAUDE.md, Git, Serena memory)
- Calculation: O(n) where n = number of phases
- Display: O(1) formatted output
- **Total time**: <1 second for typical projects

**Usage patterns:**
- Most used at start of session to check progress
- Used before resuming work to understand state
- Used after completing phase to verify progress updated
- Used before creating checkpoint to capture current state
