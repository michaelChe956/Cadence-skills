# Cadence pre-check 镜像源配置：中国大陆镜像
# 由 pre-check.sh 通过 --mirror cn 加载，仅在脚本进程内生效。
# 不写入用户全局 npm/uv/git 配置。
#
# 注意：CADENCE_SUPERPOWERS_GIT 为空格分隔的 GitHub 加速代理候选，
# 按顺序尝试，均指向上游 https://github.com/obra/superpowers。

# npm registry（淘宝镜像，影响 npx/npm 全局安装与 npx 临时包）
CADENCE_NPM_REGISTRY="https://registry.npmmirror.com"

# Python 包索引（清华镜像，影响 uv/uvx 安装与 uvx 临时包）
CADENCE_PY_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"

# Superpowers Git GitHub 加速代理候选（按顺序尝试）
CADENCE_SUPERPOWERS_GIT="https://ghfast.top/https://github.com/obra/superpowers.git https://gh-proxy.com/https://github.com/obra/superpowers.git https://mirror.ghproxy.com/https://github.com/obra/superpowers.git"

export CADENCE_NPM_REGISTRY CADENCE_PY_INDEX CADENCE_SUPERPOWERS_GIT
