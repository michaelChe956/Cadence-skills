# 会话记录：修正插件命名和版本信息

**日期**：2026-03-01
**分支**：recreate-cadence-skills
**PR**：已创建

---

## 问题发现

### 原始问题
用户发现命令被识别为 `/Cadence-skills:init` 而非期望的 `/cadence:init`

### 根本原因
`.claude-plugin/plugin.json` 中的 `name` 字段决定了命令前缀：
```json
{
  "name": "Cadence-skills",  // ← 导致命令变成 /Cadence-skills:init
  ...
}
```

### 对比参考
superpowers 的配置：
```json
{
  "name": "superpowers",  // ← 全小写，所以命令是 /superpowers:*
  ...
}
```

---

## 解决方案

### 修改内容

#### plugin.json
```json
{
  "name": "cadence",           // Cadence-skills → cadence
  "version": "0.0.1",          // 2.4.0 → 0.0.1
  "author": {
    "name": "michaelChe",      // Cadence Team → michaelChe
    "email": "michaelChe956@gmail.com"  // cadence@example.com → michaelChe956@gmail.com
  }
}
```

#### marketplace.json
```json
{
  "owner": {
    "name": "michaelChe",      // Cadence Team → michaelChe
    "email": "michaelChe956@gmail.com"
  },
  "plugins": [{
    "name": "cadence",         // Cadence-skills → cadence
    "version": "0.0.1",        // 2.4.0 → 0.0.1
    "author": {
      "name": "michaelChe",
      "email": "michaelChe956@gmail.com"
    }
  }]
}
```

---

## 影响范围

### 修改前
- 命令：`/Cadence-skills:init`
- Skill：`Cadence-skills:using-cadence`

### 修改后
- 命令：`/cadence:init`
- Skill：`cadence:using-cadence`

---

## Git 提交信息

```
fix: 修正插件命名和版本信息

- 插件名称从 "Cadence-skills" 改为 "cadence"（小写）
  * 确保命令格式为 /cadence:init 而非 /Cadence-skills:init
  * 符合 Claude Code 插件命名规范

- 版本从 "2.4.0" 调整为 "0.0.1"
  * 项目处于初始开发阶段

- 更新作者信息
  * 作者：Cadence Team → michaelChe
  * 邮箱：cadence@example.com → michaelChe956@gmail.com
```

---

## 关键知识点

### 1. Claude Code 插件命名规范
- **plugin.json 中的 `name` 字段决定命令前缀**
- 应使用**全小写**命名，避免驼峰或大写
- 格式：`/name:command`

### 2. 命名空间隔离
```
/cadence:init        ← Cadence 项目
/superpowers:init    ← superpowers 项目
```

### 3. 配置文件层次
| 文件 | 作用 |
|------|------|
| `plugin.json` | 定义插件名称、版本、作者 |
| `marketplace.json` | 定义市场和插件列表 |
| `commands/*.md` | 命令快捷映射 |

---

## 文件路径

- `.claude-plugin/plugin.json`
- `.claude-plugin/marketplace.json`
- `commands/init.md`

---

## 后续步骤

1. ✅ 修改配置文件
2. ✅ 提交代码
3. ✅ 推送到远程
4. ✅ 创建 PR
5. ⏳ 等待合并
6. ⏳ 测试命令是否正确识别为 `/cadence:init`

---

## 相关文档

- 方案2：`.claude/designs/next/方案2_元Skill_InitSkill.md`
- superpowers 参考：`/home/michael/workspace/github/superpowers`
