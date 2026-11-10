# Shell 会话环境隔离门禁（Shell Session Isolation）

> **目的**：持久化 shell 会话里的环境变量会跨命令存活；一次 `export` 污染会让后续所有命令在错误的 HOME/PATH 下运行，且症状伪装成「用户环境配置有问题」。
> **背景**：2026-11-10 为复现 CI 链接矩阵步骤，执行了 `matrix_home="$(mktemp -d)" && export HOME="$matrix_home" && …`。`export` 落在持久会话里没有随命令结束还原，之后每次 bash 调用的 `HOME` 都指向该临时目录。随后 `git config --global --list` 输出为空、`git commit` 报 `Author identity unknown`，一度被误判为「用户没配全局 git 身份」，并临时给仓库写了仓库级身份兜底。根因是会话被污染，不是用户配置缺失。

## 🔴 强制规则

### 1. 隔离环境只作用于单条命令

测试、CI 复现、隔离安装等需要临时 HOME 时，用前缀赋值或 `env`，不要 `export`：

```bash
# ✅ 正确：只影响这一条命令
HOME="$(mktemp -d)" bash tests/test-install.sh
env HOME="$(mktemp -d)" GIT_CONFIG_GLOBAL=/dev/null git status

# ❌ 错误：污染持久会话，后续命令全部受影响
export HOME="$(mktemp -d)"
```

### 2. 确需多条命令共享环境时，用子 shell 圈定作用域

```bash
# ✅ 正确：子 shell 内 export，退出即还原
(
  export HOME="$(mktemp -d)"
  bash tests/test-install.sh
)

# ❌ 错误：export 泄漏到外层会话
export HOME="$(mktemp -d)"
bash tests/test-install.sh
```

### 3. 禁止在持久会话里改会话级全局变量

`HOME`、`PATH`、`GIT_*`、`XDG_*`、`SSH_AUTH_SOCK`、`http_proxy` 等一律不得在持久会话里 `export` 长期生效。确需临时改 `PATH` 等，优先用单条命令前缀赋值；必须改时按规则 2 用子 shell。

### 4. 临时目录的生命周期不得与 HOME 指向交叉

- 临时目录用完立即 `rm -rf`。
- **不得**在 `rm` 掉临时目录之后仍让 `HOME`/`PWD` 指向它；需要保留目录时，另存路径变量并在会话结束时还原。
- 隔离命令结束后自查一次 `echo "$HOME"`，确认仍是预期值。

### 5. 出现「环境配置丢失」类症状时，先查 HOME 再下结论

| 症状 | 先查 | 不要直接下的结论 |
|------|------|------------------|
| `git config --global --list` 为空 | `echo "$HOME"` | ❌「用户没配全局身份」 |
| `git commit` 报 `Author identity unknown` | `echo "$HOME"` + `ls "$HOME/.gitconfig"` | ❌「用户配置有问题」 |
| `gh`/`ssh` 认证异常 | `echo "$HOME"` + `ls "$HOME/.ssh"` | ❌「凭据丢了」 |
| 命令找不到刚装的工具 | `echo "$PATH"` | ❌「安装失败」 |

判定为会话污染后，第一动作是恢复 `HOME` 并**撤销**基于错误前提做的临时改动（如给仓库写的仓库级 `user.name`/`user.email`），而不是保留兜底配置。

## 正确姿势速查

```bash
# 隔离 HOME 跑测试，并保证结束后不留痕迹
tmp_home="$(mktemp -d)"
HOME="$tmp_home" bash tests/test-install.sh
rm -rf -- "$tmp_home"

# 会话结束前的自检
printf 'HOME=%s\n' "$HOME"
git config --global --list | grep -E '^user\.' || echo '警告：全局 git 身份不可见'
```

## 与其他规则的关系

- 与 `ci-trigger-gating.md` 正交：本规则管会话卫生，不管 CI 触发面。
- 与 `three-platform-gating.md` 正交：本规则中的示例命令同样需兼容 macOS bash 3.2（禁 `mapfile`、`declare -A`）。
- 与 `real-machine-gating.md` 正交：真机实测里的隔离 HOME 命令同样适用规则 1、4。
