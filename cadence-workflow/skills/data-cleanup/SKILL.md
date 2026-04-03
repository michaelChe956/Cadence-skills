---
name: data-cleanup
description: Use when Serena memory storage grows large, when checkpoint data exceeds retention period, or during periodic maintenance to archive old checkpoints and delete expired data
---

# Data Cleanup - Archive and Delete Expired Data

## Overview

**Core Principle**: Automatically archive old checkpoints and delete expired data based on lifecycle policies, maintaining Serena memory performance while preserving important historical data.

Data cleanup provides:
- Automatic lifecycle management (TTL enforcement)
- Archive mechanism (preserve historical data)
- Storage optimization (prevent unlimited growth)
- Performance maintenance (keep queries fast)

## When to Use

**Use this skill when:**
- Checkpoint data exceeds TTL (30 days default)
- Progress data exceeds TTL (90 days default)
- Session Summary data exceeds TTL (180 days default)
- Serena memory storage grows large (>100 memories)
- Periodic maintenance (recommended: weekly)

**Do NOT use for:**
- Deleting active project data
- Emergency data recovery (use backup skill instead)
- Selective data deletion (use manual deletion)

## Lifecycle Policies

### Default TTL Configuration

```yaml
Lifecycle:
  checkpoint:
    ttl: 2592000                    # 30 days (seconds)
    archive_after: 604800           # 7 days → archive
    delete_after: 2592000           # 30 days → delete

  progress:
    ttl: 7776000                    # 90 days
    archive_after: 2592000          # 30 days → archive
    delete_after: 7776000           # 90 days → delete

  session_summary:
    ttl: 15552000                   # 180 days
    archive_after: 7776000          # 90 days → archive
    delete_after: 15552000          # 180 days → delete
```

### Lifecycle Phases

```
Active (0-7 days) → Archive (7-30 days) → Delete (30+ days)
       ↑                    ↑                      ↑
   Normal use         Read-only access      Permanently removed
```

## The Process

### Step 1: Scan Data Inventory

**List all memories to analyze:**

**Checkpoints:**
```bash
# List all checkpoint memories
serena list_memories --pattern "checkpoint-*"
```

**Progress records:**
```bash
# List all progress memories
serena list_memories --pattern "progress-*"
```

**Session summaries:**
```bash
# List all session memories
serena list_memories --pattern "session-*"
```

**Count and categorize:**
```markdown
Checkpoint count: {count}
Progress count: {count}
Session count: {count}
Total memories: {total}
```

### Step 2: Identify Data to Archive

**Determine which data needs archiving:**

#### Checkpoint Archive Criteria

```markdown
Archive if:
  - created_at < {archive_after} seconds ago
  - created_at > {archive_after} seconds ago AND
  - created_at < {delete_after} seconds ago
```

**Example (current date: 2026-03-06):**
```yaml
Checkpoint created: 2026-02-20  # 14 days ago
Archive after: 7 days
Delete after: 30 days

Result: ARCHIVE (7 < 14 < 30)
```

#### Progress Archive Criteria

```markdown
Archive if:
  - created_at > 30 days ago
  - created_at < 90 days ago
```

#### Session Summary Archive Criteria

```markdown
Archive if:
  - created_at > 90 days ago
  - created_at < 180 days ago
```

**Action:**
```
IF data meets archive criteria:
  → Add to archive_list
  → Log: "准备归档: {memory_name}, 创建时间: {created_at}"
```

### Step 3: Identify Data to Delete

**Determine which data needs deletion:**

#### Checkpoint Delete Criteria

```markdown
Delete if:
  - created_at > {delete_after} seconds ago
  - OR expires_at < current_time
```

**Example (current date: 2026-03-06):**
```yaml
Checkpoint created: 2026-01-15  # 50 days ago
Delete after: 30 days

Result: DELETE (50 > 30)
```

#### Progress Delete Criteria

```markdown
Delete if:
  - created_at > 90 days ago
```

#### Session Summary Delete Criteria

```markdown
Delete if:
  - created_at > 180 days ago
```

**Action:**
```
IF data meets delete criteria:
  → Add to delete_list
  → Log: "准备删除: {memory_name}, 创建时间: {created_at}"
```

### Step 4: Execute Archive Operation

**Archive identified data:**

#### Archive Single Memory

**Read original data:**
```markdown
serena read_memory --name "{memory_name}"
```

**Compress data (optional):**
```markdown
For large data:
  - Remove redundant fields
  - Compress JSON
  - Store summary only
```

**Rename to archive:**
```markdown
Old name: checkpoint-user-auth-design-uuid
New name: archive-checkpoint-user-auth-design-uuid

Naming rule: archive-{original_name}
```

**Write archived data:**
```markdown
serena write_memory --name "archive-{memory_name}" --data {data}
```

**Delete original:**
```markdown
serena delete_memory --name "{memory_name}"
```

**Update index:**
```markdown
Remove from active index
Add to archive index
```

#### Archive Batch

**Process multiple memories:**
```markdown
FOR each memory in archive_list:
  1. Read data
  2. Compress (optional)
  3. Write archive-{name}
  4. Delete original
  5. Update index

Log: "归档完成: {count} 个记忆"
```

### Step 5: Execute Delete Operation

**Delete expired data:**

#### Delete Single Memory

**Read metadata (for logging):**
```markdown
serena read_memory --name "{memory_name}"
→ Record: project_id, phase, created_at, size
```

**Delete memory:**
```markdown
serena delete_memory --name "{memory_name}"
```

**Update index:**
```markdown
Remove from all indices:
  - index-{project}-checkpoints-by-time
  - index-{project}-checkpoints-by-phase
  - index-{project}-checkpoints-by-project
```

**Log deletion:**
```markdown
"已删除: {memory_name}, 项目: {project_id}, 阶段: {phase}, 创建时间: {created_at}"
```

#### Delete Batch

**Process multiple memories:**
```markdown
FOR each memory in delete_list:
  1. Read metadata
  2. Delete memory
  3. Update index
  4. Log deletion

Log: "删除完成: {count} 个记忆"
```

### Step 6: Update Indices

**Clean up indices after archive/delete:**

#### Time Index Update

```yaml
# index-{project}-checkpoints-by-time
"2026-02-15":
  - checkpoint-user-auth-design-uuid1  # ← Remove if archived/deleted
  - checkpoint-user-auth-analyze-uuid2

Remove entry if array becomes empty
```

#### Phase Index Update

```yaml
# index-{project}-checkpoints-by-phase
"design":
  - checkpoint-user-auth-design-uuid1  # ← Remove if archived/deleted
  - checkpoint-api-refactor-design-uuid3

Remove entry if array becomes empty
```

#### Project Index Update

```yaml
# index-{project}-checkpoints-by-project
"user-auth":
  - checkpoint-user-auth-design-uuid1  # ← Remove if archived/deleted
  - checkpoint-user-auth-analyze-uuid2

Remove entry if array becomes empty
```

### Step 7: Generate Cleanup Report

**Summarize cleanup operations:**

```markdown
## 数据清理报告

**执行时间**: {current_timestamp}

### 归档统计
- **归档数量**: {archive_count}
- **归档列表**: {archive_list}
- **释放空间**: {freed_space} (估算)

### 删除统计
- **删除数量**: {delete_count}
- **删除列表**: {delete_list}
- **释放空间**: {freed_space} (估算)

### 当前状态
- **Checkpoint 总数**: {checkpoint_count}
- **Progress 总数**: {progress_count}
- **Session 总数**: {session_count}
- **Serena 内存总数**: {total_memories}

### 下次清理建议
- **建议时间**: {next_cleanup_date} (7天后)
- **预计归档**: {estimated_archive}
- **预计删除**: {estimated_delete}
```

## Quick Reference

| Operation | Criteria | Action | Index Update |
|-----------|----------|--------|--------------|
| **Archive Checkpoint** | 7-30 days old | Rename to `archive-*` | Move to archive index |
| **Delete Checkpoint** | >30 days old | Delete permanently | Remove from all indices |
| **Archive Progress** | 30-90 days old | Rename to `archive-*` | Move to archive index |
| **Delete Progress** | >90 days old | Delete permanently | Remove from all indices |
| **Archive Session** | 90-180 days old | Rename to `archive-*` | No index |
| **Delete Session** | >180 days old | Delete permanently | No index |

## Common Mistakes

### ❌ Deleting Active Data

**Problem:** Deleting data still in use

```markdown
# ❌ Wrong - no age check
checkpoint exists → delete

# ✅ Correct - verify age first
IF created_at > delete_after:
  → Delete
ELSE:
  → Keep
```

### ❌ Not Updating Indices

**Problem:** Indices point to deleted memories

```markdown
# ❌ Wrong - delete without index update
Delete memory → done

# ✅ Correct - update indices
Delete memory
→ Update time index
→ Update phase index
→ Update project index
```

### ❌ Skipping Archive Phase

**Problem:** Deleting data that should be archived first

```markdown
# ❌ Wrong - delete immediately
Checkpoint 20 days old → delete

# ✅ Correct - archive first
Checkpoint 20 days old → archive
Checkpoint 40 days old → delete
```

### ❌ Not Logging Deletions

**Problem:** No audit trail of what was deleted

```markdown
# ❌ Wrong - silent deletion
Delete memory → done

# ✅ Correct - log everything
Delete memory
→ Log: name, project, phase, created_at, deleted_at
→ Generate report
```

## Integration with Other Skills

### Periodic Cleanup in Checkpoint Skill

**Add cleanup trigger:**
```markdown
## After saving checkpoint

IF checkpoint_count > 100:
  → Call data-cleanup skill
  → Execute cleanup
  → Log cleanup results
```

### Manual Cleanup Command

**Create `/cleanup` command:**
```markdown
# /cleanup - Manual data cleanup

## Usage
/cleanup [--dry-run] [--force]

## Options
--dry-run: Show what would be cleaned without actually cleaning
--force: Skip confirmation prompt

## Process
1. Scan data inventory
2. Identify data to archive
3. Identify data to delete
4. IF not --dry-run:
   5. Execute archive
   6. Execute delete
   7. Update indices
   8. Generate report
```

## Dry Run Mode

**Test cleanup without making changes:**

```markdown
## /cleanup --dry-run

### Step 1: Scan (✓ makes no changes)
List all memories

### Step 2-3: Identify (✓ makes no changes)
Calculate which data to archive/delete

### Step 4-6: Skip (✗ skips actual changes)
Log: "DRY RUN: Would archive {count} memories"
Log: "DRY RUN: Would delete {count} memories"

### Step 7: Generate Preview Report
Show what WOULD happen
```

**Use dry run to:**
- Preview impact before cleanup
- Verify lifecycle policies
- Estimate space savings
- Plan cleanup schedule

## Red Flags - STOP Cleanup

**STOP and investigate if:**
- Data to delete includes active project
- Archive list includes recent data (<7 days)
- Delete list is unusually large (>50% of total)
- Index update fails
- Cannot read memory metadata

**Do NOT:**
- Delete data without age verification
- Skip archive phase for data in archive window
- Delete without updating indices
- Ignore dry run warnings
- Force cleanup without backup

**All of these mean: Stop, investigate, fix issue, then retry.**

## Performance Impact

### Memory Scan Performance

```
100 memories → 1-2 seconds
500 memories → 5-10 seconds
1000 memories → 10-20 seconds
```

### Cleanup Performance

```
Archive 10 memories → 5-10 seconds
Delete 10 memories → 3-5 seconds
Update indices → 2-5 seconds
Total cleanup → 10-20 seconds (per 10 memories)
```

### Recommendations

- Run cleanup weekly (not daily)
- Use dry run first to estimate impact
- Clean during low-activity periods
- Batch operations (don't clean one-by-one)
