# Tasks

## 1. OpenSpec 作用域与错误文案

- [x] 1.1 `pre-check.sh`：CLI ≥ 2.1.0 时为缺失端初始化调用显式追加项目作用域参数；更早版本不追加（对应「OpenSpec 作用域与初始化参数」）
- [x] 1.2 `pre-check.sh`：复核失败的 phase `error` 点明 2.1.0+ 默认全局作用域的原因与补救方向（对应「OpenSpec 作用域与初始化参数」）
- [x] 1.3 `SKILL.md`：说明脚本为 2.1.0+ 钉住项目作用域，Agent 不手工传入作用域参数

## 2. OpenSpec 网络超时与镜像回退

- [x] 2.1 `pre-check.sh`：2.1.0+ 的初始化与更新纳入单次超时与阶段级网络预算，超时按失败报告并写明尝试次数与下一步（对应「OpenSpec 网络调用超时与镜像回退」）
- [x] 2.2 `mirrors/cn.sh` / `default.sh`：新增 GitHub 加速代理候选配置；`pre-check.sh` 按序回退，仅改写子进程 git url 重写（对应「OpenSpec 网络调用超时与镜像回退」）
- [x] 2.3 `SKILL.md`：说明超时、预算与代理回退语义

## 3. 升级范围与镜像透传

- [x] 3.1 `pre-check.sh`：`--upgrade` 纳入 pi-mcp-adapter，经 pi 更新机制升级并沿用镜像 npm 源；固定版本不改动，版本未追到 latest 记失败（对应「升级范围与镜像透传」）
- [x] 3.2 `pre-check.sh`：pi 安装使用镜像 npm 源；codegraph 在大陆镜像下经 GitHub 加速代理取回退下载，用户已设置下载源时不覆盖（对应「升级范围与镜像透传」）
- [x] 3.3 `SKILL.md`：说明升级范围、镜像透传与"脚本不重建索引"

## 4. 验证

- [x] 4.1 新增用例覆盖：2.1.0 项目作用域钉住、复核失败文案、代理依次回退、挂起后有界失败、网络预算约束、pi 升级成功/失败/已最新/固定版本、pi 安装镜像源、codegraph 下载源改写
- [x] 4.2 `tests/test_pre_check.py`、`tests/test_projection_guard.py`、`tests/test_capture_baseline.py` 与 `scripts/test.sh` 全绿，`bash -n` 通过
- [x] 4.3 真实 CLI 验证：OpenSpec 2.1.0 经加速代理在项目根产出投影、codegraph 缺平台子包时经代理取回并缓存、pi 的 pi-mcp-adapter 由 5.4.0 升至 7.0.1
