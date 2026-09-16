# 三端兼容门禁（Three-Platform Gating）

> **目的**：本仓库产出的任何可执行内容（脚本、CI、文档示例命令、测试 fixture）必须在三端同时可用：**Linux（x64）、macOS（Intel）、macOS（Apple Silicon）**。
> **背景教训**（2026-09-16）：`install.sh` 使用 `declare -A` 与 GNU 专用 `mv -T`，在 macOS 自带 bash 3.2 + BSD 工具下三个入口全部启动失败。用户端首次运行即崩，修复成本远超编写时省下的注意成本。

## 🔴 适用范围（先查这里）

| 内容类型 | 门禁 |
|---------|------|
| `install.sh` 及任何 `.sh` 脚本 | 🔴 **三端强制**（bash 3.2 基线） |
| CI workflow（`.github/workflows/**`） | 🔴 **三端强制**（命令须同时给 Linux 与 macOS runner 跑通） |
| 测试 / fixture（含隔离 HOME 套件） | 🔴 **三端强制**（fixture 不得依赖 GNU-only 行为） |
| 文档中的示例命令（README、readmes、SKILL.md） | 🔴 **三端强制**（读者会直接复制执行） |
| 纯叙述性文档（不含可执行命令） | 🟢 免检 |

**记忆口诀：会被人复制到终端执行的内容，一律按 bash 3.2 + BSD 工具基线编写。**

## 硬性禁令（bash 层，目标基线 = macOS 自带 bash 3.2）

- ❌ `declare -A` / 关联数组 / `${!assoc[@]}` → ✅ 索引数组 + 线性查找函数（参考 `install.sh` 的 `list_has`）
- ❌ `mapfile` / `readarray` → ✅ `while IFS= read -r` 循环
- ❌ `${var,,}` / `${var^^}` / `${var^}` → ✅ `tr` / `case` 手工转换
- ❌ `&>>` 复合重定向 → ✅ `>>file 2>&1`
- ❌ `set -u` 下直接展开可能为空的数组 `"${arr[@]}"` → ✅ `${arr[@]+"${arr[@]}"}`
- ❌ `echo -e` / `echo -n` 依赖 → ✅ `printf`

## 硬性禁令（工具层，BSD/macOS 无对应行为）

| GNU 写法 | 三端安全写法 |
|----------|-------------|
| `mv -T src dst`（替换软链） | `mv -T` 失败回退 `rm -f` 临时链 + `ln -sfn`（参考 `install.sh` REPLACE 分支） |
| `sed -i 's/a/b/'` | in-place 编辑不跨平台：临时文件 `sed 's/a/b/' f > tmp && mv tmp f`，或平台分支（macOS 需 `sed -i ''`） |
| `readlink -f` | macOS 旧版无 `-f`；用 `realpath`（较新）或循环 `readlink` 归一 |
| `stat -c` / `date -d` / `grep -P` / `xargs -r` / `timeout` | `stat -f`（BSD）不通用：改用可移植替代或平台分支 |
| `mktemp` 无模板 | 始终带 `XXXXXX` 模板：`mktemp -d "${TMPDIR:-/tmp}/x.XXXXXX"` |

另注意：部分 Linux 环境的 `mv` 是 uutils 重实现（Rust 版 coreutils，如本开发机；GitHub runner 仍为 GNU）——`-T` 选项存在但对"软链→目录"目标运行时报错。凡依赖 `mv` 替换软链，必须带运行时回退，不能只探测选项是否存在。

## Intel 与 Apple Silicon 差异点（macOS 两端）

- Homebrew 前缀：Apple Silicon `/opt/homebrew`，Intel `/usr/local` → 脚本探测用 `command -v brew` 后取 `$(brew --prefix)`，禁止硬编码
- 架构分支：需要区分时用 `uname -m`（`arm64` vs `x86_64`），不用 `arch -x86_64` 探测结果做唯一依据
- 系统工具链（bash 3.2、BSD coreutils）两端一致：按上两张表写即可同时覆盖

## 验证门禁（声称三端可用前必须全部通过）

1. **本机 Linux 跑通**：改动路径的完整场景（含空输入/空数组边界）
2. **bash 3.2 容器跑通**（固定方法，已验证可用）：
   ````bash
   podman pull docker.io/library/bash:3.2
   podman run --rm -v /tmp/fake-home:/tmp/fake-home -v "$PWD/install.sh":/install.sh:ro \
     -e HOME=/tmp/fake-home -e PATH=/tmp/fake-home/bin:/usr/local/bin:/usr/bin:/bin \
     docker.io/library/bash:3.2 bash /install.sh --dry-run
   ````
   要点：挂载路径必须与 HOME 一致（否则受管链接判定失真）；容器内无 git 时在 fake-home `bin/` 放 `exit 0` stub 并置 PATH 首位
3. **macOS 真机**：按 `real-machine-gating.md` 五步走，Intel/AS 任一真机验证即可放行另一端（工具链一致），但首次引入平台分支时两端都要过
4. `shellcheck --severity=warning` 零告警（不识别版本差异，仅兜底）

## 判定有疑问时

- 默认从严：按 🔴 三端强制处理
- 拿不准某语法是否 3.2 支持：以 `podman bash:3.2` 实测为准，不查记忆

## 存量过渡（本规则生效前的已知违例）

规则只约束新写与修改的内容；以下存量违例在触碰对应文件时必须收敛为三端写法：

- `.github/workflows/ci.yml`：`mktemp -d` 无模板（L46/L53）、`mapfile -t`（L62）
- `.github/workflows/eval.yml`：`declare -A`（L87）

以上命令当前跑在 GitHub Linux runner 上侥幸可用，一旦复用进 macOS job 或本地文档即失效。
