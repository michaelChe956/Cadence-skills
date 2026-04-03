---
name: version-migration
description: Use when reading Progress or Checkpoint data with outdated version numbers, when metadata.version is older than current version, or when data format changes require field transformations
---

# Version Migration - Upgrade Data to Current Version

## Overview

**Core Principle**: Detect outdated data versions, execute migration scripts to transform data to current format, preserve data integrity through backup and rollback mechanisms.

Version migration provides:
- Automatic version detection
- Safe migration with backup
- Rollback on failure
- Version compatibility guarantee

## When to Use

**Use this skill when:**
- Reading Progress data with `metadata.version < "1.1"`
- Reading Checkpoint data with `metadata.version < "1.1"`
- Data format has changed between versions
- Field renames or type changes occurred

**Do NOT use for:**
- Same-version data (version = current)
- Manual data editing (different concern)
- Emergency data recovery (use backup skill)

## Current Versions

```yaml
Progress:
  current_version: "1.1"
  supported_versions: ["1.0", "1.1"]

Checkpoint:
  current_version: "1.1"
  supported_versions: ["1.0", "1.1"]

Task:
  current_version: "1.0"
  supported_versions: ["1.0"]
```

## The Process

### Step 1: Read Data Version

**Extract version from metadata:**

```markdown
1. Read data from Serena memory
2. Extract metadata.version field
3. Compare with current_version
```

**Version comparison logic:**
```
IF data.version == current_version:
  → No migration needed
  → Return data as-is

IF data.version < current_version:
  → Migration required
  → Continue to Step 2

IF data.version > current_version:
  → Error: future version
  → Cannot process
  → Return error
```

### Step 2: Create Backup

**Before any migration, backup original data:**

```markdown
## Backup naming convention
Original: progress-{project_id}
Backup: backup-progress-{project_id}-{timestamp}

Original: checkpoint-{project_id}-{phase}-{uuid}
Backup: backup-checkpoint-{project_id}-{phase}-{uuid}-{timestamp}
```

**Backup steps:**
```markdown
1. Read original data
2. Create backup copy with timestamp
3. Verify backup integrity
4. Log backup creation
```

**Backup integrity check:**
```markdown
Backup created → Read backup → Compare with original
IF mismatch:
  → Delete backup
  → Abort migration
  → Return error: "Backup failed, aborting migration"
```

### Step 3: Determine Migration Path

**Identify which migration scripts to run:**

#### Migration Chain Example

```yaml
# Version history
1.0 → 1.1: Add time_stats field
1.1 → 1.2: Rename phases to stages (future)

# Migration path for 1.0 → 1.1
Path: 1.0 → 1.1 (single step)

# Migration path for 1.0 → 1.2 (future)
Path: 1.0 → 1.1 → 1.2 (two steps)
```

**Migration path logic:**
```
IF data.version == "1.0" AND current_version == "1.1":
  → Migration path: [migrate_1_0_to_1_1]

IF data.version == "1.0" AND current_version == "1.2":
  → Migration path: [migrate_1_0_to_1_1, migrate_1_1_to_1_2]
```

### Step 4: Execute Migration

**Run migration scripts in order:**

#### Migration: 1.0 → 1.1 (Progress)

**Changes:**
```yaml
# Added field
time_stats:
  total_time: 0
  estimated_remaining: 0

# Default value
IF NOT exists time_stats:
  → Add time_stats with default values
```

**Migration script:**
```markdown
## migrate_progress_1_0_to_1_1

INPUT: progress_data (v1.0)

Step 1: Add time_stats field
IF "time_stats" NOT IN progress_data:
  progress_data.time_stats = {
    "total_time": 0,
    "estimated_remaining": 0
  }

Step 2: Update version
progress_data.metadata.version = "1.1"

Step 3: Update timestamp
progress_data.metadata.updated_at = current_timestamp

OUTPUT: progress_data (v1.1)
```

#### Migration: 1.0 → 1.1 (Checkpoint)

**Changes:**
```yaml
# Added field
ttl: 2592000  # 30 days

# Added field
expires_at: calculated from created_at + ttl

# Default value
IF NOT exists ttl:
  → Add ttl with default value
IF NOT exists expires_at:
  → Calculate from created_at + ttl
```

**Migration script:**
```markdown
## migrate_checkpoint_1_0_to_1_1

INPUT: checkpoint_data (v1.0)

Step 1: Add ttl field
IF "ttl" NOT IN checkpoint_data:
  checkpoint_data.ttl = 2592000  # 30 days

Step 2: Add expires_at field
IF "expires_at" NOT IN checkpoint_data:
  created_at = checkpoint_data.created_at
  ttl = checkpoint_data.ttl
  checkpoint_data.expires_at = created_at + ttl

Step 3: Update version
checkpoint_data.metadata.version = "1.1"

Step 4: Update timestamp
checkpoint_data.timestamp = current_timestamp

OUTPUT: checkpoint_data (v1.1)
```

### Step 5: Validate Migrated Data

**Ensure migration produced valid data:**

```markdown
## Validation checklist

1. Call data-validation skill
2. Verify all required fields present
3. Verify field types correct
4. Verify value ranges valid
5. Verify version updated to current_version
```

**Validation logic:**
```
validation_result = data-validation(migrated_data)

IF validation_result.valid == false:
  → Migration failed
  → Rollback to backup
  → Return error: "Migration validation failed: {errors}"

IF validation_result.valid == true:
  → Migration successful
  → Continue to Step 6
```

### Step 6: Save Migrated Data

**Write migrated data to Serena memory:**

```markdown
1. Write migrated data to original memory name
2. Overwrite old data
3. Verify write success
4. Delete backup (optional, or keep for safety)
```

**Save logic:**
```
write_result = serena.write_memory(
  name: original_name,
  data: migrated_data
)

IF write_result.success:
  → Log: "Migration successful: {original_name} v{old_version} → v{new_version}"
  → Delete backup (optional)
  → Return migrated_data

IF write_result.failed:
  → Rollback to backup
  → Return error: "Failed to save migrated data"
```

### Step 7: Rollback on Failure

**If any step fails, restore from backup:**

**Rollback triggers:**
- Backup creation failed
- Migration script error
- Validation failed
- Save failed

**Rollback procedure:**
```markdown
1. Read backup data
2. Write backup to original name
3. Verify restoration
4. Delete backup
5. Log rollback
```

**Rollback logging:**
```markdown
## 迁移失败，已回滚

**数据名称**: {original_name}
**原版本**: {old_version}
**目标版本**: {target_version}
**失败原因**: {failure_reason}
**回滚时间**: {rollback_timestamp}

**建议操作**:
- 检查数据格式是否符合预期
- 手动修复数据后重试
- 联系支持获取帮助
```

## Quick Reference

| Step | Action | Success | Failure |
|------|--------|---------|---------|
| **1. Read version** | Extract metadata.version | Continue to Step 2 | Error if future version |
| **2. Create backup** | backup-{name}-{timestamp} | Continue to Step 3 | Abort migration |
| **3. Determine path** | Identify migration chain | Continue to Step 4 | Error if no path |
| **4. Execute migration** | Run migration scripts | Continue to Step 5 | Rollback |
| **5. Validate data** | Call data-validation | Continue to Step 6 | Rollback |
| **6. Save data** | Write to Serena | Success, delete backup | Rollback |
| **7. Rollback** | Restore from backup | Log and return error | Critical error |

## Migration Registry

### Progress Migrations

| From | To | Changes | Script |
|------|----|---------|--------|
| 1.0 | 1.1 | Add time_stats field | migrate_progress_1_0_to_1_1 |

### Checkpoint Migrations

| From | To | Changes | Script |
|------|----|---------|--------|
| 1.0 | 1.1 | Add ttl, expires_at fields | migrate_checkpoint_1_0_to_1_1 |

### Future Migrations (Example)

```yaml
# Planned: 1.1 → 1.2
Changes:
  - Rename phases to stages
  - Add stage_dependencies field
  - Change percentage to progress_percentage

Script: migrate_progress_1_1_to_1_2
Status: Not implemented (future)
```

## Common Mistakes

### ❌ Migrating Without Backup

**Problem:** Data loss if migration fails

```markdown
# ❌ Wrong - no backup
Read data → Migrate → Save

# ✅ Correct - backup first
Read data → Backup → Migrate → Validate → Save → Delete backup
```

### ❌ Skipping Validation

**Problem:** Invalid data after migration

```markdown
# ❌ Wrong - no validation
Migrate → Save

# ✅ Correct - validate after migration
Migrate → Validate → IF valid: Save ELSE: Rollback
```

### ❌ Not Updating Version Number

**Problem:** Infinite migration loop

```markdown
# ❌ Wrong - version not updated
Add fields → Save

# ✅ Correct - update version
Add fields → Update version to 1.1 → Save

Result: Next read won't trigger migration again
```

### ❌ Migrating Same Version

**Problem:** Unnecessary work, potential data corruption

```markdown
# ❌ Wrong - always migrate
Read data → Migrate → Save

# ✅ Correct - check version first
Read data
IF version < current:
  → Migrate
ELSE:
  → Use as-is
```

## Integration with Other Skills

### Auto-Migration on Read

**In status skill:**
```markdown
### Step 1: Read Progress Data

1. Call serena read_memory
2. Call version-migration skill to check version
3. IF migration needed:
     → Auto-migrate
     → Save migrated data
4. Use migrated data for display
```

**In checkpoint skill:**
```markdown
### Step 1: Read Checkpoint Data

1. Call serena read_memory
2. Call version-migration skill
3. IF migration needed:
     → Auto-migrate
     → Save migrated data
4. Continue with checkpoint operations
```

### Manual Migration Command

**Create `/migrate` command:**
```markdown
# /migrate - Manual version migration

## Usage
/migrate {memory_name} [--backup] [--dry-run]

## Options
--backup: Keep backup after migration (default: delete)
--dry-run: Show what would be migrated without making changes

## Process
1. Read memory
2. Detect version
3. IF --dry-run:
     → Show migration plan
     → Stop
4. Create backup
5. Execute migration
6. Validate
7. Save
8. IF NOT --backup:
     → Delete backup
9. Report results
```

## Dry Run Mode

**Test migration without making changes:**

```markdown
## /migrate progress-user-auth --dry-run

### Step 1: Read Data (✓ makes no changes)
Read progress-user-auth
Current version: 1.0

### Step 2: Determine Migration (✓ makes no changes)
Migration path: 1.0 → 1.1
Script: migrate_progress_1_0_to_1_1

### Step 3: Preview Changes (✓ makes no changes)
Would add field: time_stats.total_time = 0
Would add field: time_stats.estimated_remaining = 0
Would update version: 1.0 → 1.1

### Step 4-6: Skip (✗ skips actual changes)
DRY RUN: Would backup, migrate, validate, and save

### Report
Migration would succeed
Estimated time: 2-3 seconds
```

## Red Flags - STOP Migration

**STOP and investigate if:**
- Data version is future version (> current_version)
- Backup creation fails
- Migration script error
- Validation fails after migration
- Cannot save migrated data

**Do NOT:**
- Migrate without backup
- Skip validation
- Ignore migration errors
- Continue after validation failure
- Delete backup if save failed

**All of these mean: Rollback, investigate, fix issue, then retry.**

## Version Compatibility Strategy

### Backward Compatibility

```yaml
# Can read old versions
Supported versions: ["1.0", "1.1"]

# Reading v1.0 data
Read → Detect v1.0 → Migrate to v1.1 → Use v1.1
```

### Forward Compatibility

```yaml
# Cannot read future versions
IF version > current_version:
  → Error: "Future version detected, cannot process"
  → Suggest: "Update skills to support version {version}"
```

### Version Bump Rules

**Minor version bump (1.0 → 1.1):**
- Add new optional fields
- Add default values
- No breaking changes
- Old code can still read

**Major version bump (1.x → 2.0):**
- Remove fields
- Rename fields
- Change types
- Breaking changes
- Old code cannot read

**Current strategy:**
- Only minor version bumps
- Maintain backward compatibility
- Auto-migrate on read
- No breaking changes
