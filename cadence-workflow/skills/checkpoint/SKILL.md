---
name: checkpoint
description: Use when completing a phase, before resuming work, or creating a recovery point for interrupted workflows
---

# Checkpoint - Save Progress Snapshot

## Overview

**Core Principle**: Create a complete snapshot of current state, save to Serena memory with unique ID, and update all related records and indices.

A checkpoint captures the complete state at a specific point in time:
- Git context (branch, commits)
- TodoWrite state (tasks)
- Project context (metadata)
- Phase information (current status)

Checkpoints enable:
- Recovery from interruptions
- Progress tracking
- State auditing

## When to Use

**Use this skill when:**
- Completing a phase (automatically triggered)
- Before resuming interrupted work
- Creating a recovery point before risky changes
- Saving state for later analysis

**Do not use for:**
- Viewing current progress (use `/status` instead)
- Generating reports (use `/report` instead)
- Real-time monitoring (use `/monitor` instead)

## Data Model

### Checkpoint Structure

```yaml
Checkpoint:
  metadata:
    version: "1.0"
    checkpoint_id: string  # UUID v4
    project_id: string

  phase: string
  task_id: string | null
  status: "completed" | "in_progress" | "failed"
  timestamp: string  # ISO 8601

  context:
    git_branch: string
    git_commits: string[]  # Last 10 commits
    todowrite_state: object[]  # All current tasks
    project_context: object  # From CLAUDE.md

  output: string | null  # Output file path

  ttl: number  # 30 days (2592000 seconds)
  created_at: string
  expires_at: string
```

### Memory Naming Convention

**Format**: `checkpoint-{project_id}-{phase}-{uuid}`

**Examples**:
- `checkpoint-user-auth-design-550e8400-e29b-41d4-a716-446655440000`
- `checkpoint-api-refactor-brainstorm-a1b2c3d4-e5f6-7890`

**Why this format?**
- `project_id`: Isolate checkpoints by project
- `phase`: Filter by development phase
- `uuid`: Guarantee global uniqueness

### Related Records

**Progress Record** (`progress-{project_id}`):
```yaml
phases:
  - phase_name: "design"
    status: "in_progress"
    # Updated with checkpoint info
```

**Indices** (updated when checkpoint created):
```yaml
# Time index
index-{project_id}-checkpoints-by-time:
  "2026-03-04":
    - "checkpoint-user-auth-design-uuid1"
    - "checkpoint-user-auth-analyze-uuid2"

# Phase index
index-{project_id}-checkpoints-by-phase:
  "design":
    - "checkpoint-user-auth-design-uuid1"
  "analyze":
    - "checkpoint-user-auth-analyze-uuid2"
```

## The Process

### Step 1: Gather Context

**Read Git information:**
```bash
# Current branch
git branch --show-current

# Recent commits (last 10)
git log --oneline -10

# Working directory status
git status --short
```

**Read TodoWrite state:**
```markdown
1. List all tasks
2. Capture task IDs, subjects, statuses
3. Include dependencies if any
```

**Read project context:**
```markdown
1. Read .claude/CLAUDE.md
2. Extract:
   - Project name
   - Project ID
   - Project description
   - Current phase
   - Flow type (full-flow/quick-flow/exploration-flow)
```

### Step 2: Generate Unique Checkpoint ID

**Generate UUID v4:**
```bash
# Using Python
python3 -c 'import uuid; print(str(uuid.uuid4()))'

# Or using macOS
uuidgen

# Output example: 550e8400-e29b-41d4-a716-446655440000
```

**Why UUID v4?**
- 128-bit random ID
- Virtually no collisions
- Standard format supported everywhere

### Step 3: Build Checkpoint Data

**Assemble checkpoint structure:**
```yaml
metadata:
  version: "1.0"
  checkpoint_id: "{uuid}"
  project_id: "{from CLAUDE.md or directory name}"

phase: "{current phase}"
task_id: "{current task ID or null}"
status: "{phase status}"
timestamp: "{current ISO 8601}"

context:
  git_branch: "{current branch}"
  git_commits: ["{commit1}", "{commit2}", ...]
  todowrite_state: [{task1}, {task2}, ...]
  project_context: {project info}

output: "{output file path or null}"

ttl: 2592000  # 30 days
created_at: "{current timestamp}"
expires_at: "{created_at + 30 days}"
```

### Step 3.5: Validate Checkpoint Data (REQUIRED)

**🔴 CRITICAL: Validate data before saving**

**Call data-validation skill:**
```markdown
Call: data-validation skill
Input: checkpoint_data

IF validation fails:
  → STOP checkpoint creation
  → Log validation errors
  → Return error to user
  → DO NOT proceed to Step 4

IF validation passes:
  → Continue to Step 4
```

**Validation checklist:**
- ✅ All required fields present
- ✅ Field types correct
- ✅ UUID format valid
- ✅ Enum values valid
- ✅ Timestamps in ISO 8601 format
- ✅ TTL > 0

**Why validation is REQUIRED:**
- Prevents corrupted data in Serena memory
- Ensures all checkpoints can be read by other skills
- Catches errors early (before they cause cascading failures)

### Step 3.6: Acquire Resource Lock (REQUIRED for Concurrency Safety)

**🔴 CRITICAL: Acquire lock before writing to prevent concurrent conflicts**

**Call lock-utils skill:**
```markdown
Call: lock-utils skill (Acquire Lock)
Parameters:
  resource_name: "progress-{project_id}"
  task_id: "checkpoint-{phase}"
  ttl: 300  # 5 minutes

IF lock acquisition fails:
  → STOP checkpoint creation
  → Log error: "Failed to acquire lock for {resource_name}"
  → Return error to user
  → DO NOT proceed to Step 4

IF lock acquisition succeeds:
  → Continue to Step 4
  → Remember to release lock in Step 8 (REQUIRED)
```

**Why lock is REQUIRED:**
- Prevents concurrent writes to Progress record
- Ensures data consistency
- Avoids race conditions in multi-session scenarios

### Step 3.7: Begin Transaction - Create Backups (REQUIRED for Data Integrity)

**🔴 CRITICAL: Create backups before writing to ensure atomicity**

**Call transaction-utils skill:**
```markdown
Call: transaction-utils skill (Begin Transaction)
Parameters:
  critical_resources:
    - "progress-{project_id}"
    - "index-{project_id}-checkpoints-by-time"
    - "index-{project_id}-checkpoints-by-phase"
  operation_description: "checkpoint-{phase}"

## Backup Process:
FOR each resource IN critical_resources:

  1. Read existing data
     existing_data = call Serena read_memory
       memory_name: "{resource}"

  2. Create backup
     IF existing_data 存在:
       backup_name = "backup-{resource}-{timestamp}"
       call Serena write_memory
         memory_name: "{backup_name}"
         content: {
           resource_name: "{resource}",
           backup_data: existing_data,
           backup_at: get_current_timestamp(),
           operation: "checkpoint-{phase}"
         }

     ELSE:
       ## Record resource doesn't exist (first creation)
       backup_data = null

IF backup creation fails:
  → STOP checkpoint creation
  → Release lock (Step 8)
  → Log error: "Failed to create backup for {resource}"
  → Return error to user
  → DO NOT proceed to Step 4

IF backup creation succeeds:
  → Continue to Step 4
  → Remember to rollback or commit in Step 8 (REQUIRED)
```

**Why backup is REQUIRED:**
- Ensures atomicity of multi-step operations
- Allows rollback if any step fails
- Prevents partial updates (some succeed, some fail)
- Guarantees data consistency

### Step 4: Save to Serena Memory

**Save checkpoint data:**
```markdown
Call: mcp__serena__write_memory
Parameters:
  memory_name: "checkpoint-{project_id}-{phase}-{uuid}"
  content: {checkpoint YAML/JSON}
  max_chars: -1 (use default)
```

**Example:**
```
memory_name: "checkpoint-user-auth-design-550e8400-e29b-41d4-a716-446655440000"
```

### Step 5: Update Progress Record

**Read progress record:**
```markdown
Call: mcp__serena__read_memory
Parameter: memory_name = "progress-{project_id}"
```

**Update phase information:**
```yaml
phases:
  - phase_name: "{current phase}"
    status: "{new status}"
    end_time: "{current timestamp}"  # if completed
```

**Save updated progress:**
```markdown
Call: mcp__serena__write_memory
Parameters:
  memory_name: "progress-{project_id}"
  content: {updated progress data}
```

### Step 6: Update Indices

**Update time index:**
```markdown
1. Read index: index-{project_id}-checkpoints-by-time
2. Add checkpoint ID to today's date
3. Save index

Example:
index-user-auth-checkpoints-by-time:
  "2026-03-04":
    - "checkpoint-user-auth-design-uuid1"
    - "checkpoint-user-auth-analyze-uuid2"
```

**Update phase index:**
```markdown
1. Read index: index-{project_id}-checkpoints-by-phase
2. Add checkpoint ID to phase
3. Save index

Example:
index-user-auth-checkpoints-by-phase:
  "design":
    - "checkpoint-user-auth-design-uuid1"
```

**Update project index:**
```markdown
1. Read index: index-checkpoints-by-project
2. Add checkpoint ID to project
3. Save index

Example:
index-checkpoints-by-project:
  "user-auth":
    - "checkpoint-user-auth-design-uuid1"
```

### Step 7: Display Confirmation

**Show checkpoint details:**
```
✅ Checkpoint created successfully!

Checkpoint ID: 550e8400-e29b-41d4-a716-446655440000
Memory: checkpoint-user-auth-design-550e8400-e29b-41d4-a716-446655440000
Phase: design
Status: in_progress
Expires: 2026-04-03 15:30:00Z
```

### Step 7.5: Handle Transaction - Commit or Rollback (REQUIRED for Atomicity)

**🔴 CRITICAL: Commit or rollback transaction before releasing lock**

**Decision Logic:**
```markdown
IF all operations (Steps 4-7) succeeded:
  → Call transaction-utils skill (Commit Transaction)
  → Continue to Step 8

IF any operation (Steps 4-7) failed:
  → Call transaction-utils skill (Rollback Transaction)
  → Continue to Step 8
```

#### Option A: Commit Transaction (Success Path)

**Call transaction-utils skill:**
```markdown
Call: transaction-utils skill (Commit Transaction)

## Commit Process:
1. Confirm all operations succeeded
   - Checkpoint saved ✅
   - Progress updated ✅
   - Indices updated ✅

2. Optionally cleanup temporary backups
   FOR each backup IN created_backups:
     call Serena delete_memory
       memory_name: "{backup_name}"

   Note: Backup cleanup is optional
   - Success path: can cleanup to save space
   - Failure path: keep for debugging

3. Mark transaction as committed
   → Log: "Transaction committed for checkpoint-{phase}"
```

#### Option B: Rollback Transaction (Failure Path)

**Call transaction-utils skill:**
```markdown
Call: transaction-utils skill (Rollback Transaction)

## Rollback Process:
1. Reverse traverse all backups (REVERSE order)
   FOR backup IN reverse(created_backups):
     call Serena read_memory
       memory_name: "{backup_name}"

     IF backup.backup_data == null:
       ## Resource was newly created
       call Serena delete_memory
         memory_name: "{backup.resource_name}"

     ELSE:
       ## Resource already existed
       call Serena write_memory
         memory_name: "{backup.resource_name}"
         content: backup.backup_data

2. Verify rollback success
   FOR each restored resource:
     verify = call Serena read_memory
       memory_name: "{resource_name}"

     IF verify != backup.backup_data:
       → Log CRITICAL error: "Rollback failed for {resource_name}"
       → Manual intervention required

3. Log rollback completion
   → Log: "Transaction rolled back for checkpoint-{phase}"
   → Return error to user
```

**Example - Rollback Sequence:**
```markdown
假设操作失败在 Step 5 (更新Progress):

备份资源（创建顺序）:
  1. progress-user-auth
  2. index-user-auth-checkpoints-by-time
  3. index-user-auth-checkpoints-by-phase

已完成操作:
  4. ✅ Checkpoint saved
  5. ❌ Progress update failed

回滚顺序（反向）:
  1. 删除 Checkpoint (新创建) - 因为是新资源
  2. 恢复 index-checkpoints-by-phase (已备份)
  3. 恢复 index-checkpoints-by-time (已备份)
  4. 恢复 progress-user-auth (已备份)

结果: 所有数据恢复到操作前状态
```

**Why transaction handling is REQUIRED:**
- Ensures atomicity (all or nothing)
- Prevents partial updates
- Guarantees data consistency
- Allows recovery from failures

### Step 8: Release Resource Lock (REQUIRED - Always Execute)

**🔴 CRITICAL: Release lock in finally block**

**Call lock-utils skill:**
```markdown
Call: lock-utils skill (Release Lock)
Parameters:
  resource_name: "progress-{project_id}"
  task_id: "checkpoint-{phase}"

IF lock release fails:
  → Log error: "Failed to release lock for {resource_name}"
  → This is a CRITICAL error (lock will timeout after TTL)
  → Continue anyway (checkpoint was saved successfully)

IF lock release succeeds:
  → Lock released successfully
  → Checkpoint creation complete
```

**⚠️ IMPORTANT: Always execute in finally block**
```markdown
try:
  Step 3.6: Acquire lock
  Step 4: Save checkpoint
  Step 5: Update progress
  Step 6: Update indices
  Step 7: Display confirmation

finally:
  Step 8: Release lock (ALWAYS)
    → Even if previous steps failed
    → Prevents lock from being held indefinitely
    → Lock will auto-timeout after TTL as fallback
```

**Why release is REQUIRED:**
- Allows other tasks to access the resource
- Prevents deadlocks
- Ensures system remains responsive

## Quick Reference

### Checkpoint Creation Checklist

| Step | Action | Tool | Required |
|------|-------|------|----------|
| 1 | Gather context | Git, TodoWrite, CLAUDE.md | ✅ Yes |
| 2 | Generate UUID | Python `uuid.uuid4()` | ✅ Yes |
| 3 | Build checkpoint | Assemble YAML/JSON | ✅ Yes |
| 3.5 | Validate data | data-validation skill | ✅ Yes |
| **3.6** | **Acquire lock** | **lock-utils skill** | **✅ Yes (CRITICAL)** |
| **3.7** | **Begin transaction (backup)** | **transaction-utils skill** | **✅ Yes (CRITICAL)** |
| 4 | Save checkpoint | `mcp__serena__write_memory` | ✅ Yes |
| 5 | Update progress | Read → modify → write | ✅ Yes |
| 6 | Update indices | Time, phase, project | ✅ Yes |
| 7 | Display confirmation | Console output | ✅ Yes |
| **7.5** | **Commit or rollback transaction** | **transaction-utils skill** | **✅ Yes (CRITICAL)** |
| **8** | **Release lock** | **lock-utils skill** | **✅ Yes (REQUIRED)** |

### Memory Names

| Type | Format | Example |
|------|-------|---------|
| Checkpoint | `checkpoint-{project}-{phase}-{uuid}` | checkpoint-user-auth-design-550e8400... |
| Progress | `progress-{project}` | progress-user-auth |
| Time Index | `index-{project}-checkpoints-by-time` | index-user-auth-checkpoints-by-time |
| Phase Index | `index-{project}-checkpoints-by-phase` | index-user-auth-checkpoints-by-phase |
| Project Index | `index-checkpoints-by-project` | index-checkpoints-by-project |

## Code Example

### Creating Checkpoint

```python
import uuid
from datetime import datetime, timedelta
import json

# Step 1: Gather context
git_branch = "feature/user-auth"
git_commits = ["abc1234", "def5678", "ghi9012", "jkl3456"]
todowrite_state = [
    {"id": "1", "subject": "Design auth flow", "status": "completed"},
    {"id": "2", "subject": "Design hashing", "status": "in_progress"}
]
project_context = {
    "name": "User Auth",
    "phase": "design",
    "flow_type": "full-flow"
}

# Step 2: Generate UUID
checkpoint_id = str(uuid.uuid4())
project_id = "user-auth"
phase = "design"

# Step 3: Build checkpoint
now = datetime.now()
checkpoint = {
    "metadata": {
        "version": "1.0",
        "checkpoint_id": checkpoint_id,
        "project_id": project_id
    },
    "phase": phase,
    "task_id": "2",
    "status": "in_progress",
    "timestamp": now.isoformat(),
    "context": {
        "git_branch": git_branch,
        "git_commits": git_commits,
        "todowrite_state": todowrite_state,
        "project_context": project_context
    },
    "output": "cadence/designs/2026-03-04_设计方案_认证流程_v1.0.md",
    "ttl": 2592000,
    "created_at": now.isoformat(),
    "expires_at": (now + timedelta(days=30)).isoformat()
}

# Step 4: Save to Serena (pseudocode)
memory_name = f"checkpoint-{project_id}-{phase}-{checkpoint_id}"
"
write_memory(memory_name, checkpoint)

# Step 5: Update progress (pseudocode)
progress = read_memory(f"progress-{project_id}")
progress["phases"].append({
    "phase_name": phase,
    "status": "in_progress",
    "start_time": now.isoformat()
})
write_memory(f"progress-{project_id}", progress)

# Step 6: Update indices (pseudocode)
# Time index
time_index = read_memory(f"index-{project_id}-checkpoints-by-time") or {}
today = now.strftime("%Y-%m-%d")
time_index[today] = time_index.get(today, [])
time_index[today].append(memory_name)
write_memory(f"index-{project_id}-checkpoints-by-time", time_index)

# Phase index
phase_index = read_memory(f"index-{project_id}-checkpoints-by-phase") or {}
phase_index[phase] = phase_index.get(phase, [])
phase_index[phase].append(memory_name)
write_memory(f"index-{project_id}-checkpoints-by-phase", phase_index)

# Step 7: Display
print(f"✅ Checkpoint created successfully!")
Checkpoint ID: {checkpoint_id}
Memory: {memory_name}")
```

## Common Mistakes

### ❌ Using timestamp instead of UUID

```python
# ❌ BAD: Not unique, can collide
checkpoint_id = f"checkpoint-{int(time.time())}"
```

**Problem**: Multiple checkpoints created at same second will have same ID

```python
# ✅ GOOD: UUID guarantees uniqueness
checkpoint_id = str(uuid.uuid4())
```

### ❌ Missing context

```python
# ❌ BAD: Only saving phase name
checkpoint = {
    "phase": "design",
    "timestamp": now.isoformat()
}
```

**Problem**: Can't recover state later

```python
# ✅ GOOD: Complete context
checkpoint = {
    "metadata": {...},
    "phase": "design",
    "context": {
        "git_branch": branch,
        "git_commits": commits,
        "todowrite_state": tasks,
        "project_context": project
    },
    ...
}
```

### ❌ Not updating progress record

```python
# ❌ BAD: Only saving checkpoint
write_memory(checkpoint_name, checkpoint)
# Done!
```

**Problem**: Progress record doesn't reflect checkpoint

```python
# ✅ GOOD: Update related records
write_memory(checkpoint_name, checkpoint)
progress = read_memory(progress_name)
# Update progress
write_memory(progress_name, progress)
# Update indices
write_memory(index_name, index)
```

### ❌ Wrong naming convention

```python
# ❌ BAD: Hard to query
memory_name = f"checkpoint-{timestamp}"
```

**Problem**: Can't filter by project or phase

```python
# ✅ GOOD: Follows convention
memory_name = f"checkpoint-{project_id}-{phase}-{uuid}"
```

## Red Flags

**STOP and reconsider if:**
- Using timestamp for ID (use UUID)
- Not saving all context (save everything)
- Not updating progress (update progress record)
- Not updating indices (indices enable fast queries)
- Wrong memory name format (follow convention)
- Skipping UUID generation (UUID is required)
- **🔴 Skipping lock acquisition (REQUIRED for concurrency safety)**
- **🔴 Not releasing lock (MUST release in finally block)**
- **🔴 Lock acquisition failed but continuing anyway (STOP and retry)**
- **🔴 Forgetting to call lock-utils skill (REQUIRED for all writes)**

## Integration Points

 **Automatically triggered** by:
- Phase completion (in flow skills)
- Before resuming work (in resume skill)
- Manual checkpoint creation (via `/checkpoint` command)

**Updates**:
- Progress record (progress-{project_id})
- Time index (index-{project_id}-checkpoints-by-time)
- Phase index (index-{project_id}-checkpoints-by-phase)
- Project index (index-checkpoints-by-project)

## Testing Checklist

Before deploying:
- [ ] Generates UUID v4 (not timestamp)
- [ ] Collects Git branch + commits
- [ ] Collects TodoWrite state
- [ ] Collects project context
- [ ] Validates checkpoint data (Step 3.5)
- [ ] **Acquires lock before writing (Step 3.6)**
- [ ] Memory name: checkpoint-{project}-{phase}-{uuid}
- [ ] Updates progress record
- [ ] Updates time index
- [ ] Updates phase index
- [ ] Updates project index
- [ ] Output shows checkpoint ID and location
- [ ] Sets TTL (30 days)
- [ ] **Releases lock after completion (Step 8)**
- [ ] **Lock released even if operation fails (finally block)**

### Concurrency Testing
- [ ] Single checkpoint creation works correctly
- [ ] Lock acquisition prevents concurrent writes
- [ ] Lock release allows subsequent operations
- [ ] Lock timeout prevents permanent deadlocks
- [ ] Multiple checkpoints in sequence work correctly
