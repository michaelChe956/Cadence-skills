# Tasks: rule-config-self-contained-templates

## 1. 测试先行（TDD 红）

- [ ] 1.1 重写 pytest `TestLocateTemplates`：删六用例，新增三用例——完整 skill 目录命中（patch `SKILL_DIR` 到完整 fixture）；缺件 `TemplateError` 且报告缺失清单；空 HOME 仍命中 skill 目录（映射「模板与脚本必须同源」全部三个 scenario）
- [ ] 1.2 反转 shell `it-s2-templates-missing`（C16e）为正断言：空 HOME 下 apply 正常完成、overall 非 fail；删除 `ONLINE_TEMPLATE_SKILL` fixture 搭建
- [ ] 1.3 新增 naruto 式回归用例：fake marketplace 旧模板 + skill 目录新模板共存，断言按 skill 目录模板收敛（映射「模板始终取自调用来源的 skill 目录」scenario）

## 2. 脚本实现（TDD 绿）

- [ ] 2.1 引入模块级 `SKILL_DIR` 常量；`_load_reference`/`_load_kernel_source` 改用常量
- [ ] 2.2 重写 `locate_templates()` 为单源定位 + 成对校验 + `TemplateError`（缺失清单与重装建议）；删除 `_ONLINE_RULES_SUBPATH`/`_OFFLINE_RULES_SUBPATH`/`_FALLBACK_GLOB_PATTERN` 与三级逻辑

## 3. 文档与对账

- [ ] 3.1 重写 `SKILL.md` 第一步定位规则为 skill 自包含表述
- [ ] 3.2 重写 `references/merge-semantics.md` §11.5 为单源定位契约
- [ ] 3.3 同步 `tests/skill-clause-map.md` 的 S1b-01~04 行（三级定位 → 单源；it-s2-templates-missing 语义反转登记）

## 4. 全量验证

- [ ] 4.1 pytest 全量通过
- [ ] 4.2 shell 生命周期套件全量通过
- [ ] 4.3 E2E：模拟过期 marketplace 共存环境，验证模板按 skill 目录收敛且 `document-storage.md` 被归档+覆盖
