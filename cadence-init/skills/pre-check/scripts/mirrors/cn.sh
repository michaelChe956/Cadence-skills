# Cadence pre-check 镜像源配置：中国大陆镜像
# 由 pre-check.sh 通过 --mirror cn 加载，仅在脚本进程内生效。
# 不写入用户全局 npm/uv/git 配置。
#
# 注意：CADENCE_SUPERPOWERS_GIT 指向用户自行同步维护的国内 Git 镜像，
# 需定期与上游 https://github.com/obra/superpowers 同步。

# npm registry（淘宝镜像，影响 npx/npm 全局安装与 npx 临时包）
CADENCE_NPM_REGISTRY="https://registry.npmmirror.com"

# Python 包索引（清华镜像，影响 uv/uvx 安装与 uvx 临时包）
CADENCE_PY_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"

# Superpowers Git 国内镜像（用户自行同步）
CADENCE_SUPERPOWERS_GIT="https://gitee.com/michaelChe-World/superpowers.git"

export CADENCE_NPM_REGISTRY CADENCE_PY_INDEX CADENCE_SUPERPOWERS_GIT
