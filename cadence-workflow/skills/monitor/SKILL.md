---
name: monitor
description: Use when checking current task status quickly, viewing a snapshot of progress, or monitoring active development work
---

# Monitor - View Progress Snapshot

## Overview

**Core Principle**: Call status skill to get current progress, then display in the monitor.md format with a note about it being a snapshot.

**

Monitor provides a quick status check that:
- Shows current phase and task
- Displays progress percentage
- Shows time elapsed
- Provides next steps

**Important**: This is a one-time snapshot, not real-time monitoring. Claude Code does not support background tasks or automatic refresh. Run `/monitor` again to see updated status.

**

## When to Use

**Use this skill when:**
- Checking current task status
- Getting a quick progress overview
- Viewing what's happening right now
- Monitoring active development work

**Do not use for:**
- Detailed progress reports (use `/report` instead)
- Creating checkpoints (use `/checkpoint` instead)
- Resuming interrupted work (use `/resume` instead)

- Real-time continuous monitoring (not possible in Claude Code)

## Limitation

**⚠️ Not Real-Time Monitoring**

Claude Code does not support:
- Background tasks
- Timers
- Automatic refresh

**What this skill does:**
- Calls `/status` once
- Formats output
- Shows snapshot
- Returns immediately

**To update**: Run `/monitor` again

## The Process

### Step 1: Call Status Skill

**Invoke status skill:**
```markdown
Call: status skill
Parameters: (none - uses current project context)
```

The status skill will:
- Read project information
- Read progress data
- Calculate progress
- Format output

### Step 2: Add Monitor Note

**Append to status output:**
```markdown
---
⏰ Snapshot captured at {current_timestamp}

💡 This is a one-time status snapshot. To see updates, run /monitor again.
 The status does not update in real-time.
```

### Step 3: Display Result

**Show formatted output:**
```
📊 [status output from /status]
+
⏰ Snapshot captured at 2026-03-04 16:30:00
💡 This is a one-time status snapshot. To see updates, run /monitor again.
 The status does not update in real-time.
```

## Quick Reference
### Monitor vs Status vs Report

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `/monitor` | Quick snapshot | Check current status quickly |
| `/status` | Detailed status | Full progress overview |
| `/report` | Complete history | Document work done, create report file |

### Output Format

```
📊 Project Progress: {project_name}

## Current Task
- **Task**: {current_task}
- **Status**: {status}
- **Started**: {start_time}
- **Elapsed**: {elapsed_time}

## Overall Progress
[████████░░░] {percentage}% ({completed}/{total} phases)

⏰ Snapshot captured at {timestamp}
💡 This is a one-time status snapshot. To see updates, run /monitor again.
 The status does not update in real-time.
```

## Code Example

```python
from datetime import datetime

# Step 1: Call status skill
status_output = invoke_skill("status")

# Step 2: Add monitor note
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
monitor_note = f"""
---
⏰ Snapshot captured at {timestamp}

💡 This is a one-time status snapshot. To see updates, run /monitor again. The status does not update in real-time.
 """
"""

# Step 3: Combine and display
output = status_output + "\n" + monitor_note
 print(output)
```

## Common Mistakes

### ❌ Promising Real-Time Monitoring

```markdown
# ❌ BAD: Misleading users
This command monitors your progress in real-time and updates every 5 seconds.
```

**Problem**: Claude Code cannot run background tasks or Cannot deliver on promise

```markdown
# ✅ GOOD: Clear about limitations
This is a one-time snapshot. Run /monitor again to see updates.
 The status does not update in real-time.
```

### ❌ Not Calling Status Skill

```python
# ❌ BAD: Duplicating logic
def monitor():
    progress = read_memory("progress-...")
    # Calculate percentage... (duplicate code)
    # Format output... (duplicate code)
```

**Problem**: Code duplication, maintenance burden

```python
# ✅ GOOD: Reuse status skill
def monitor():
    output = invoke_skill("status")
    output += "\n⏰ Snapshot captured at...\\n💡 This is a one-time snapshot..."
    print(output)
```

### ❌ Not Adding Snapshot Note

```markdown
# ❌ BAD: Users expect real-time updates
📊 Progress: 50%
[No note about snapshot]
```

**Problem**: Users will wait for updates that never come

```markdown
# ✅ GOOD: Clear expectations
📊 Progress: 50%
⏰ Snapshot captured at 16:30:00
💡 This is a one-time status snapshot. Run /monitor again to see updates.
 The status does not update in real-time.
```

## Red Flags

**STOP if you**
- Implementing real-time monitoring logic (not possible)
- Duplicating status skill logic (reuse instead)
- Not clarifying snapshot nature (misleads users)
- Missing timestamp (users don't know when snapshot was taken)
- Not instructing users to run again (confusing UX)

## Testing Checklist

Before deploying:
- [ ] Calls status skill correctly
- [ ] Adds snapshot note
- [ ] Includes timestamp in note
- [ ] Clarifies it one-time nature
- [ ] Instructs users to run again for updates
- [ ] Output format matches monitor.md format
- [ ] Does not implement real-time monitoring logic
