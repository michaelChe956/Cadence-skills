# 技术栈检测与写入移除报告

## 范围

本轮按已更新契约执行“全删”：rule-config 不再检测项目技术栈，也不再在入口文件生成或更新技术栈、包管理器、命令、覆盖率字段；`## 项目配置` 仅维护产物自动提交开关。

## 代码变更

- 删除 `_detect_tech_stack`，`detect_project` 仅返回 `project_type` 与 `evidence`；S1 不再写入 `report["tech_stack"]`。
- 删除 `_ensure_techstack_block`、`PLACEHOLDER_VALUES` 及所有技术栈差异动作；`_compose_entry` 返回 `(text, warnings)`，移除 `tech_stack` 参数并同步所有调用点。
- S4 入口合成仅执行 L0、强制规则章节规范化和提交开关归并；已有 `### 项目技术栈`、`### 包管理器规则` 等用户内容不参与脚本管理，逐字保留。
- 项目配置章节缺失时由 `_ensure_commit_toggle` 创建，说明改为 `> 以下配置由初始化脚本维护。`。
- dry-run planned warnings 预演同步移除技术栈输入，报告 schema 不再包含技术栈字段。

## 测试变更

- 删除纯技术栈检测/写入测试、双入口技术栈一致测试及相关旧 `_compose_entry` 技术栈参数。
- 新增两个守护测试：既有用户技术栈块逐字保留且开关落位；无技术栈入口不生成技术栈字段。
- 保留入口 E2E 的规则、Serena、L0、KB 内容和开关断言；移除技术栈断言。
- 生命周期脚本移除已失效的技术栈写入场景及 skip-summary 对技术栈生成的断言。

## 文档同步

同步更新 `SKILL.md`、`references/merge-semantics.md`、`tests/skill-clause-map.md`、根 README 和已更新 OpenSpec 契约：项目配置仅维护开关，既有技术栈用户内容保留，脚本不检测/写入技术栈。

## 验证

- `python3 -m unittest discover -s cadence-init/skills/rule-config/tests -v`：212/212 通过（移除技术栈专属测试，并保留/补回非技术栈 S4 摘要回填回归后的数量）。
- `bash cadence-init/skills/rule-config/tests/verify-managed-lifecycle.sh`：`SUMMARY pass=103 fail=0`；移除 1 个技术栈写入场景后 pass 数由 104 降为 103，无失败。
- `python3 -m py_compile cadence-init/skills/rule-config/scripts/rule-config.py cadence-init/skills/rule-config/tests/test_rule_config.py`：通过。

## 残余风险

历史 review/brief 产物仍可能包含已废弃的技术栈检测描述；这些是历史审计材料，不属于现行 SKILL、references、测试或实现范围。
