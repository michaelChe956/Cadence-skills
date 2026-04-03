---
name: report
description: Use when generating project progress reports, creating development summaries, or documenting development work
---

# Report - Generate Progress Report

## Overview

**Core Principle**: Collect data from multiple sources, calculate statistics, generate formatted markdown report, and save to `.claude/reports/`.

Reports provide:
- Session summary (completed phases)
- Checkpoint history (all saved states)
- Git commit history (work done)
- Statistics (completion rate, time spent, etc.)

## When to Use

**Use this skill when:**
- Completing a project or phase
- Documenting work done
- Creating development summary
- Generating handoff documentation

- End of sprint review

- Creating release notes

**Do not use for:**
- Viewing current progress (use `/status` instead)
- Creating checkpoints (use `/checkpoint` instead)
- Real-time monitoring (use `/monitor` instead)

## Report Types

### Full Report
Complete project history with all details

**Includes**:
- Session summary (flow type, phases completed)
- All checkpoints (with full details)
- All Git commits (with messages)
- Detailed statistics (time per phase, test coverage)
- Output files (documents created)
- Next steps (what's left)

### Phase Report
Focus on specific development phase

**Includes**:
- Phase overview (what was done)
- Checkpoints created (during this phase)
- Commits made (during this phase)
- Phase statistics (time spent, completion rate)
- Phase outputs (documents created)
- Next steps for next phase

### Session Report
High-level overview without detailed checkpoints

**Includes**:
- Overall progress percentage
- Phases completed vs pending
- Total time spent
- Estimated time remaining
- Key achievements
- Blockers encountered

## The Process

### Step 1: Collect Data

**Read session data:**
```markdown
Call: mcp__serena__read_memory
Parameter: memory_name = "progress-{project_id}"

Returns: progress data with:
- Session metadata
- Phase information
- Overall progress
- Time statistics
```

**Read checkpoint data:**
```markdown
Call: mcp__serena__list_memories
Parameter: topic = "checkpoint-{project_id}"

For each checkpoint_name in memories:
    checkpoint = read_memory(checkpoint_name)
    checkpoints.append(checkpoint)
```

**Read Git commit history:**
```bash
# Get commits for checkpoint date range
git log --oneline --since {start_date}

git log --oneline --since {end_date}
```

**Read output files:**
```markdown
For each phase:
    if phase["output"]:
        output_files.append(phase["output"])
```

### Step 2: Calculate Statistics

**Calculate phase statistics:**
```python
for phase in phases:
    if phase["status"] == "completed":
        # Calculate duration
        if phase["start_time"] and phase["end_time"]:
            duration = parse_time(phase["end_time"]) - parse_time(phase["start_time"])
            phase["duration"] = duration

        # Count commits
        phase["commit_count"] = count_commits_between_dates(phase["start_time"], phase["end_time"])

```

**Calculate overall statistics:**
```python
total_time = sum(phase["duration"] for phase in phases if phase["duration"])
avg_time_per_phase = total_time / completed_phases
estimated_remaining = avg_time_per_phase * (total_phases - completed_phases)
```

**Calculate test statistics:**
```markdown
For each completed phase:
    if phase["test_result"]:
        # Count passed/failed
        test_stats["passed"] += 1 if phase["test_result"] == "passed"
        test_stats["failed"] += 1 if phase["test_result"] == "failed"

        # Calculate coverage
        if phase["coverage"]:
            coverage_scores.append(phase["coverage"])

test_pass_rate = test_stats["passed"] / (test_stats["passed"] + test_stats["failed"]) * 100
 if test_stats["passed"] + test_stats["failed"] > 0 else 100.0
 avg_coverage = sum(coverage_scores) / len(coverage_scores) if coverage_scores else 0
 avg_test_coverage = None
```

### Step 3: Generate Report

**Create report structure:**
```markdown
# Report header
report = f"# Development Report: {project_name}\n\n"
report += f"**Generated**: {timestamp}\n"
report += f"**Flow Type**: {flow_type}\n\n"

# Session Summary
report += "## Session Summary\n\n"
report += "- **Started**: {created_at}\n"
report += "- **Last Updated**: {updated_at}\n"
report += "- **Progress**: {percentage}% ({completed_phases}/{total_phases} phases)\n"
report += "- **Status**: {status} (completed/in_progress/paused)\n\n"

# Phase Breakdown
report += "## Phase Breakdown\n\n"
for phase in phases:
    emoji = "✅❌🔄⏳"[phase['status']]
    report += f"### {phase['phase_name']}\n"
    report += f"- **Status**: {phase['status']}\n"
    report += f"- **Started**: {format_time(phase['start_time'])}\n"

    if phase['end_time']:
        report += f"- **Completed**: {format_time(phase['end_time'])}\n"
        report += f"- **Duration**: {duration}\n"
    if phase['commit_count']:
        report += f"- **Commits**: {phase['commit_count']}\n"
    if phase['test_result']:
        report += f"- **Tests**: {phase['test_result']}\n"
    if phase['coverage']:
        report += f"- **Coverage**: {phase['coverage']}%\\n"
    if phase['output']:
        report += f"- **Output**: `{phase['output']}\n"
    report += "\n"

# Statistics
report += "## Statistics\n\n"
report += f"- **Total Time**: {total_time}\n"
report += f"- **Avg Time/Phase**: {avg_time_per_phase}\n"
report += f"- **Estimated Remaining**: {estimated_remaining}\n"
if test_stats:
    report += f"- **Test Pass Rate**: {test_pass_rate}%\n"
    if avg_coverage:
        report += f"- **Avg Coverage**: {avg_coverage}%\n"

# Checkpoints
report += "## Checkpoints\n\n"
report += f"Total Checkpoints: {len(checkpoints)}\\n\n"
for checkpoint in checkpoints:
    report += f"### {checkpoint['phase']} - {format_time(checkpoint['timestamp'])}\n"
    report += f"- Phase: {checkpoint['phase']}\n"
    report += f"- Status: {checkpoint['status']}\n"
    report += "\n"

# Git History
report += "## Git History\n\n"
report += "```\n"
{git log output}
\n"
report += "```\n"

# Output Files
report += "## Output Files\n\n"
for file in output_files:
    report += f"- {file}\n"
    report += "\n"

# Next Steps
report += "## Next Steps\n\n"
report += f"{next_steps}\n"
```

**Save report:**
```markdown
# Generate filename
filename = f".claude/reports/{date}_开发报告_{project_name}_v1.0.md"

example: 2026-03-04_开发报告_user-auth_v1.0.md

# Write report
write_file(filename, report)
```

### Step 4: Display Summary

**Show report location:**
```
✅ Report generated successfully!

Location: {filename}
```

## Quick Reference
### Report Structure

| Section | Content |
|--------|---------|
| Header | Title, date, flow type |
| Session Summary | Overall progress, time range |
| Phase Breakdown | One section per phase |
| Statistics | Totals, averages |
| Checkpoints | All saved checkpoints |
| Git History | All commits |
| Output Files | Documents created |
| Next Steps | What's next |

### File Naming Convention

**Format**: `YYYY-MM-DD_开发报告_{project_name}_v1.0.md`

**Examples**:
- `2026-03-04_开发报告_user-auth_v1.0.md`
- `2026-03-03_开发报告_api-refactor_v1.0.md`
- `2026-03-02_阶段报告_brainstorm_v1.0.md`

## Code Example

### Generating Full Report

```python
from datetime import datetime

# Step 1: Collect data
progress_data = read_memory("progress-user-auth")
checkpoints = list_memories(topic="checkpoint-user-auth")
commits = [
    "abc1234 - Complete brainstorm",
    "def5678 - Complete analyze",
    "ghi9012 - Complete requirement",
    "jkl3456 - Start design"
]

output_files = [
    ".claude/docs/2026-03-04_需求文档_用户认证_v1.0.md",
    ".claude/designs/2026-03-04_设计方案_认证流程_v1.0.md"
]

# Step 2: Calculate statistics
total_phases = 8
completed_phases = 3
total_time = 5 * 3600  # 5 hours
avg_time = 100  # 100 minutes
test_pass_rate = 100  # All tests passed
avg_coverage = 85  # average 85%

estimated_remaining = 8.3  # 8.3 hours * 3 remaining phases

next_steps = [
    "Complete design phase",
    "Run design review",
    "Create implementation plan",
    "Start implementation"
]

# Step 3: Generate report
filename = f".claude/reports/{datetime.now().strftime('%Y-%m-%d')}_开发报告_user-auth.md"
report = f"""# Development Report: User Authentication System

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Flow Type**: full-flow

## Session Summary
- **Started**: 2026-03-04 09:00:00
- **Last Updated**: 2026-03-04 15:30:00
- **Progress**: 37.5% (3/8 phases)
- **Status**: In Progress

## Phase Breakdown
✅ brainstorm - Completed (2h)
✅ analyze - Completed (1.5h)
✅ requirement - Completed (1.5h)
🔄 design - In Progress (30m)
⏳ design-review - Pending
⏳ plan - Pending
⏳ using-git-worktrees - Pending
⏳ subagent-development - Pending

## Statistics
- **Total Time**: 5h
- **Avg Time/Phase**: 1h 40m
- **Estimated Remaining**: 8.3h
- **Test Pass Rate**: 100%
- **Avg Coverage**: 85%
## Checkpoints
Total Checkpoints: 3
### brainstorm - 2026-03-04 11:00:00
- Phase: brainstorm
- Status: completed
### analyze - 2026-03-04 13:00:00
- Phase: analyze
- Status: completed
### requirement - 2026-03-04 15:00:00
- Phase: requirement
- Status: completed
## Git History
4 commits:
- abc1234 - Complete brainstorm: user authentication requirements
- def5678 - Complete analyze: existing code patterns
- ghi9012 - Complete requirement: auth specifications
- jkl3456 - Start design: authentication architecture
## Output Files
- .claude/docs/2026-03-04_需求文档_用户认证_v1.0.md
- .claude/designs/2026-03-04_设计方案_认证流程_v1.0.md
## Next Steps
1. Complete design phase
2. Run design review
3. Create implementation plan
4. Start implementation
"""
# Step 4: Save report
write_file(filename, report)

print(f"✅ Report generated: {filename}")
```

## Common Mistakes

### ❌ Missing Session Data

```python
# ❌ BAD: No progress data
report = generate_report()
```

**Problem**: Cannot generate report without progress data

```python
# ✅ GOOD: Read progress data first
progress = read_memory("progress-user-auth")
if not progress:
    print("No progress data found")
    return

report = generate_full_report(progress)
```

### ❌ Not Calculating Statistics

```python
# ❌ BAD: Just lists phases without statistics
for phase in phases:
    print(f"- {phase['name']}: {phase['status']}")
```

**Problem**: Report lacks insight (time spent, averages)
```python
# ✅ GOOD: Calculate and show statistics
for phase in phases:
    duration = calculate_duration(phase)
    print(f"- {phase['name']}: {phase['status']} ({duration})")
```

### ❌ Not Saving Report to File

```python
# ❌ BAD: Just prints report
print(report_content)
```

**Problem**: Report is lost when session ends
```python
# ✅ GOOD: Save to file
filename = generate_filename()
write_file(filename, report_content)
print(f"Report saved: {filename}")
```

## Red Flags

**STOP if:**
- No progress data found (start a new workflow)
- No checkpoints found (no history to report)
  - Missing statistics data (cannot calculate)
  - Output file errors (check paths validity)
  - Cannot write file (check permissions)
  - Wrong date format in filename (use YYYY-mm-dd)

## Testing Checklist

Before deploying:
- [ ] Reads progress data
- [ ] Reads checkpoint data
- [ ] Reads Git history
- [ ] Identifies output files
- [ ] Calculates phase statistics
- [ ] calculates overall statistics
- [ ] generates markdown report
- [ ] saves to `.claude/reports/`
- [ ] filename follows convention: `YYYY-MM-DD_开发报告_{project_name}_v1.0.md`
- [ ] displays confirmation with file location
