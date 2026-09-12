# Tasks: devbox 第一期

> 逐任务完整步骤与命令见 `cadence/plans/2026-09-11_计划文档_实施_devbox第一期_v1.0.md`（Task 0–10 一一对应）；本文件为高层工作包索引，任务号与计划文档一致。

- [ ] T0 前置检查（podman ≥6.1.1 / uv / bash / 设计文档 v1.6 齐备，目标目录不存在）——验收：`precondition OK`（计划 Task 0 Step 1）
- [ ] T1 devbox 目录骨架 + `devbox/versions.env`（ARG pin 唯一来源，8 个版本号 2026-09-11 实证）——验收：可 source 且 8 键齐全（计划 Task 1 Step 3）
- [ ] T2 `devbox/render-auth.py`（TDD：`parse_config`/`validate`/`render_all` + CLI `--config --home`；五端渲染 + 原子替换 + 中文报错带行号不回显 key）——验收：`tests/devbox/test_render_auth.py` 先红后绿（计划 Task 2）
- [ ] T3 `devbox/stack/stack-lib.sh` + `stack.sh`（TDD：9 个子命令，`CADENCE_STACK_DIR`，CHANGES.md 留痕行格式）——验收：`tests/devbox/test_stack_lib.py` 先红后绿（计划 Task 3）
- [ ] T4 `devbox/Dockerfile` L1–L4（国内源全 ARG pin，镜像五路径布局 + `/opt/cadence/versions.txt`）——验收：podman build 成功且 versions.txt 完整（计划 Task 4；实跑见 T9 Step 1）
- [ ] T5 `devbox/compose.yaml` + `devbox/stack/` catalog 官方模板（mysql/redis/rabbitmq/minio，external 卷 + 127.0.0.1 + profile 矩阵）——验收：`tests/devbox/test_compose_stack.py` 先红后绿（计划 Task 5）
- [ ] T6 `devbox/entrypoint.sh`（git 对齐 → render-auth 拒启 exit 2 → stack 模板同步 → skills 软失败 → `exec "$@"`）——验收：`tests/devbox/test_entrypoint.py` 先红后绿 + T9 Step 2/3 实跑（计划 Task 6）
- [ ] T7 `cadence-init/skills/devbox-stack/SKILL.md`（中间件/app 操作必须走 stack 命令；环境检测 `test -d /cadence/stack && command -v stack`）——验收：契约合规且经 install.sh find 机制自动投影实证（计划 Task 7）
- [ ] T8 `devbox/install.ps1` + `cadence-box.yaml.example`（Windows ≤5 步：Docker Desktop 引导 → 模板生成 → daemon.json 镜像源 → `up -d`）——验收：静态审查通过（本机无 pwsh），真机腿并入验收 1 移交（计划 Task 8）
- [ ] T9 本地 podman 冒烟（构建 / 鉴权失败路径 exit 2 / entrypoint 全链路 / stack 命令 / 体积门）——验收：五端 6 文件断言 OK、pi 无 packages、stack 三命令输出正确、压缩体积 ≤1GB、单测回归全绿；多容器联调为环境项（计划 Task 9，Step 7 需用户点头）
- [ ] T10 收尾 `devbox/README.md` + Windows 真机验收清单（设计文档「七」6 条逐条化，T9 实测数字回填）——验收：全文无占位符、`uv run --with pytest --with pyyaml python -m pytest tests/devbox/ -v` 37 项全绿、真机清单与移交状态汇报（计划 Task 10）
