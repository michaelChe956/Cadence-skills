# Cadence pre-check 镜像源配置：通用官方源
# 由 pre-check.sh 通过 --mirror default（默认）加载，仅在脚本进程内生效。
# 不写入用户全局 npm/uv/git 配置。

# npm registry（影响 npx/npm 全局安装与 npx 临时包）
CADENCE_NPM_REGISTRY="https://registry.npmjs.org"

# Python 包索引（影响 uv/uvx 安装与 uvx 临时包）
CADENCE_PY_INDEX="https://pypi.org/simple"

# Superpowers Git 远端地址（SKILL.md 的 Superpowers 步骤 clone/pull 使用）
CADENCE_SUPERPOWERS_GIT="https://github.com/obra/superpowers"

export CADENCE_NPM_REGISTRY CADENCE_PY_INDEX CADENCE_SUPERPOWERS_GIT
