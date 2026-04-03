---
name: data-validation
description: Use when writing Progress or Checkpoint data to Serena memory, before saving any data to ensure format correctness, required fields presence, and value range compliance
---

# Data Validation - Validate Progress and Checkpoint Data

## Overview

**Core Principle**: Validate data against JSON Schema before writing to Serena memory, reject invalid data with clear error messages, and ensure data quality at the source.

Data validation prevents:
- Missing required fields causing read failures
- Type mismatches breaking Skills execution
- Invalid values causing unexpected behavior
- Inconsistent data format across sessions

## When to Use

**Use this skill when:**
- Writing Progress data to Serena memory
- Writing Checkpoint data to Serena memory
- Updating existing Progress or Checkpoint records
- Before any data persistence operation

**Do NOT use for:**
- Reading data validation (handled by individual Skills)
- User input validation (different concern)
- Business logic validation (beyond data format)

## Data Models

### Progress Data Model

```yaml
Progress:
  metadata:
    version: "1.0"                    # Required, format: X.Y
    project_id: string                # Required, non-empty
    project_name: string              # Required, non-empty
    flow_type: string                 # Required, enum: full-flow, quick-flow, exploration-flow
    created_at: timestamp             # Required, ISO 8601
    updated_at: timestamp             # Required, ISO 8601

  project_info:
    name: string                      # Required, non-empty
    current_phase: string             # Required, non-empty
    git_branch: string                # Required, non-empty

  phases:
    - phase_name: string              # Required
      status: string                  # Required, enum: completed, in_progress, pending
      start_time: timestamp | null    # Optional
      end_time: timestamp | null      # Optional
      tasks: Task[]                   # Optional

  overall_progress:
    percentage: number                # Required, range: 0-100
    completed_phases: number          # Required, >= 0
    total_phases: number              # Required, >= 0

  time_stats:
    total_time: number                # Required, >= 0 (seconds)
    estimated_remaining: number       # Required, >= 0 (seconds)
```

### Checkpoint Data Model

```yaml
Checkpoint:
  metadata:
    version: "1.0"                    # Required, format: X.Y
    checkpoint_id: string             # Required, UUID v4 format
    project_id: string                # Required, non-empty

  phase: string                       # Required, valid phase name
  task_id: string | null              # Optional
  status: string                      # Required, enum: completed, in_progress, failed
  timestamp: string                   # Required, ISO 8601

  context:
    git_branch: string                # Required
    git_commits: string[]             # Required, array of commit SHAs
    todowrite_state: object[]         # Required, array of task objects
    project_context: object           # Required

  output: string | null               # Optional, file path

  ttl: number                         # Required, > 0 (seconds)
  created_at: string                  # Required, ISO 8601
  expires_at: string                  # Required, ISO 8601
```

## The Process

### Step 1: Identify Data Type

**Determine what you're validating:**
- Progress data → Use Progress validation rules
- Checkpoint data → Use Checkpoint validation rules

### Step 2: Validate Required Fields

**Check all required fields are present:**

#### Progress Required Fields:
```markdown
- metadata.version
- metadata.project_id
- metadata.project_name
- metadata.flow_type
- metadata.created_at
- metadata.updated_at
- project_info.name
- project_info.current_phase
- project_info.git_branch
- overall_progress.percentage
- overall_progress.completed_phases
- overall_progress.total_phases
- time_stats.total_time
- time_stats.estimated_remaining
```

#### Checkpoint Required Fields:
```markdown
- metadata.version
- metadata.checkpoint_id
- metadata.project_id
- phase
- status
- timestamp
- context.git_branch
- context.git_commits
- context.todowrite_state
- context.project_context
- ttl
- created_at
- expires_at
```

**Validation action:**
```
IF any required field missing:
  → Stop validation
  → Return error: "缺少必填字段: {field_path}"
  → Do NOT write data
```

### Step 3: Validate Field Types

**Check field types match expected:**

| Field | Expected Type | Validation |
|-------|--------------|------------|
| version | string | Matches regex `^\d+\.\d+$` |
| percentage | number | 0-100 range |
| timestamp | string | Valid ISO 8601 format |
| ttl | number | Positive integer |
| git_commits | array | Non-empty array |
| flow_type | string | One of: full-flow, quick-flow, exploration-flow |
| status (phase) | string | One of: completed, in_progress, pending |
| status (checkpoint) | string | One of: completed, in_progress, failed |

**Validation action:**
```
IF type mismatch:
  → Stop validation
  → Return error: "字段类型错误: {field_path}, 期望 {expected_type}, 实际 {actual_type}"
  → Do NOT write data
```

### Step 4: Validate Value Ranges

**Check values are within valid ranges:**

| Field | Valid Range | Invalid Example |
|-------|------------|----------------|
| percentage | 0-100 | -5, 150 |
| completed_phases | >= 0 | -1 |
| total_phases | >= 0 | -1 |
| total_time | >= 0 | -100 |
| estimated_remaining | >= 0 | -50 |
| ttl | > 0 | 0, -30 |

**Validation action:**
```
IF value out of range:
  → Stop validation
  → Return error: "字段值超出范围: {field_path}, 值: {value}, 有效范围: {valid_range}"
  → Do NOT write data
```

### Step 5: Validate Enum Values

**Check enum fields have valid values:**

#### Progress flow_type:
- ✅ Valid: `full-flow`, `quick-flow`, `exploration-flow`
- ❌ Invalid: `fast-flow`, `standard`, `custom`

#### Progress phase status:
- ✅ Valid: `completed`, `in_progress`, `pending`
- ❌ Invalid: `done`, `running`, `waiting`

#### Checkpoint status:
- ✅ Valid: `completed`, `in_progress`, `failed`
- ❌ Invalid: `success`, `error`, `cancelled`

#### Checkpoint phase:
- ✅ Valid: `brainstorm`, `analyze`, `requirement`, `design`, `design-review`, `plan`, `git-worktrees`, `subagent-development`
- ❌ Invalid: `implementation`, `coding`, `testing`

**Validation action:**
```
IF invalid enum value:
  → Stop validation
  → Return error: "无效的枚举值: {field_path}, 值: {value}, 有效值: {valid_values}"
  → Do NOT write data
```

### Step 6: Validate UUID Format (Checkpoint only)

**Check checkpoint_id is valid UUID v4:**

**Valid UUID v4 format:**
```
xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
where x is any hex digit and y is one of 8, 9, a, or b
```

**Examples:**
- ✅ Valid: `550e8400-e29b-41d4-a716-446655440000`
- ❌ Invalid: `550e8400-e29b-51d4-a716-446655440000` (version 5, not 4)
- ❌ Invalid: `550e8400e29b41d4a716446655440000` (missing hyphens)
- ❌ Invalid: `not-a-uuid` (wrong format)

**Validation action:**
```
IF invalid UUID:
  → Stop validation
  → Return error: "无效的 UUID 格式: {checkpoint_id}"
  → Do NOT write data
```

### Step 7: All Validations Passed

**If all validations pass:**
```
→ Return: {"valid": true, "errors": []}
→ Continue with write operation
```

## Quick Reference

| Validation Step | What to Check | Error Action |
|----------------|--------------|--------------|
| **Required fields** | All mandatory fields present | Reject, return error |
| **Field types** | String, number, array, object | Reject, return error |
| **Value ranges** | Numbers within valid range | Reject, return error |
| **Enum values** | Match predefined list | Reject, return error |
| **UUID format** | Valid UUID v4 (Checkpoint) | Reject, return error |

## Common Mistakes

### ❌ Missing Nested Required Fields

**Problem:** Only checking top-level fields

```yaml
# ❌ Wrong - missing nested field check
project_info exists → OK

# ✅ Correct - check nested fields
project_info.name exists → OK
project_info.current_phase exists → OK
project_info.git_branch exists → OK
```

### ❌ Not Validating Array Contents

**Problem:** Checking array exists but not contents

```yaml
# ❌ Wrong - array exists but might be empty
git_commits exists → OK

# ✅ Correct - check array non-empty
git_commits exists AND length > 0 → OK
```

### ❌ Accepting Invalid Enum Variations

**Problem:** Being too lenient with enum values

```yaml
# ❌ Wrong - accepting synonyms
status: "done" → OK (should be "completed")

# ✅ Correct - strict enum validation
status: "completed" → OK
status: "done" → ERROR
```

### ❌ Skipping Validation for "Simple" Updates

**Problem:** Assuming updates don't need validation

```markdown
# ❌ Wrong - skipping validation for updates
Just updating percentage → skip validation

# ✅ Correct - always validate
Any write operation → validate first
```

## Integration with Other Skills

### Use Before Writing Data

**In checkpoint skill:**
```markdown
### Step 3: Validate Checkpoint Data
Call data-validation skill to validate Checkpoint data

IF validation fails:
  → Log error
  → Stop checkpoint creation
  → Return error to user

IF validation passes:
  → Continue with Step 4
```

**In status skill:**
```markdown
### Step 2: Validate Progress Data
Call data-validation skill to validate Progress data before update

IF validation fails:
  → Log error
  → Stop progress update
  → Return error to user

IF validation passes:
  → Continue with Step 3
```

## Error Message Format

**Use consistent error message format:**

```markdown
## 数据验证失败

**验证步骤**: {step_name}
**失败字段**: {field_path}
**错误类型**: {error_type}
**详细信息**: {details}

**期望值**: {expected}
**实际值**: {actual}

**建议操作**: {suggested_action}
```

**Example:**
```markdown
## 数据验证失败

**验证步骤**: 必填字段检查
**失败字段**: metadata.project_id
**错误类型**: 缺少必填字段
**详细信息**: Progress 数据必须包含 project_id

**期望值**: 非空字符串
**实际值**: null

**建议操作**: 在 CLAUDE.md 中定义 project_id 或使用 Git 仓库名称生成
```

## Red Flags - STOP Validation

**STOP and reject data if:**
- Missing any required field
- Type mismatch cannot be auto-corrected
- Value out of valid range
- Invalid enum value (no guessing)
- UUID format incorrect
- Array field is empty when non-empty required

**Do NOT:**
- Try to "fix" invalid data automatically
- Write data with validation errors
- Skip validation "just this once"
- Accept "close enough" enum values

**All of these mean: Reject data, return error, let caller fix it.**
