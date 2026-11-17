# Proposal

## Why

OpenSpec CLI 2.1.0（2026-11-17 发布）改变了初始化语义，pre-check 的既有契约失效，且失败方式对用户不可解释：

1. **作用域默认变了。** 2.1.0 的初始化默认把技能装进用户家目录的全局作用域（`~/.agents/skills`），项目根只剩 `openspec/` 骨架。pre-check 仍按旧约定调用初始化，于是四端复核必然失败，报错只写"OpenSpec 客户端投影数量或路径复核失败"，用户既看不到原因，也拿不到补救动作。该失败在"项目里删掉了此前安装的技能"后才出现，因为 2.1.0 的作用域解析会优先命中项目内已有技能。

2. **2.1.0 的初始化与更新需要克隆 GitHub，而 CLI 自身没有任何网络超时。** 大陆网络下这一步会无限挂起，表现为 pre-check 卡住而不是明确失败；`--mirror cn` 只切 npm 与 pip 源，覆盖不到它。

3. **升级范围与镜像透传不一致。** `--upgrade` 覆盖 ast-grep、codegraph、openspec 与 uv，却排除了 pi-mcp-adapter，用户的 pi-mcp-adapter 会长期停留在旧版本；pi 的安装与 codegraph 在镜像缺少平台子包时的回退下载都不会走当前镜像源。

## What Changes

- pre-check 在探测到 OpenSpec CLI ≥ 2.1.0 时，为缺失客户端的初始化调用显式钉住项目作用域；更早版本不追加该参数，保持原调用不变。
- 复核失败的 phase `error` 在点明原因为"2.1.0+ 默认全局作用域"的同时给出补救方向。
- OpenSpec CLI ≥ 2.1.0 的初始化与更新纳入单次超时与阶段级网络预算，超时按失败报告，不再无限挂起；`--mirror cn` 时按序经 GitHub 加速代理访问，仅改写该次子进程的 git url 重写，不写任何 git 配置。
- `--upgrade` 的范围纳入 pi-mcp-adapter，经 pi 自带的更新机制升级并沿用当前镜像的 npm 源；固定版本写法视为用户的有意选择，不改动。
- pi 的安装与 codegraph 的外网回退下载跟随当前镜像：pi 内部 npm 使用镜像源，codegraph npm shim 的下载源在大陆镜像下经 GitHub 加速代理，用户已自行设置时不覆盖。
- 脚本继续不执行 codegraph 的初始化、索引与同步，索引仍由后续阶段决定。

## Capabilities

### Modified Capabilities

- `pre-check-scripted-execution`: 新增 OpenSpec 作用域与初始化参数、OpenSpec 网络调用超时与镜像回退、升级范围与镜像透传三项 requirement；统一性能验收与网络熔断 requirement 增加"OpenSpec 重试不得使整体超出熔断上限"的场景。

## Impact

- `cadence-init/skills/pre-check/scripts/pre-check.sh`、`scripts/mirrors/cn.sh`、`scripts/mirrors/default.sh`、`SKILL.md`。
- `cadence-init/skills/pre-check/tests/`：测试替身扩展与新增用例。
- 主 spec `pre-check-scripted-execution`。
- 无 **BREAKING** 契约变更：五阶段顺序、报告结构、失败语义、投影判定与基线守卫均不变；新增约束只作用于 OpenSpec CLI ≥ 2.1.0 与 `--upgrade` 路径。
