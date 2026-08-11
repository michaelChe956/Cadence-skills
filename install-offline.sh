#!/bin/bash
################################################################################
# Cadence Skills 离线安装脚本 (Linux/macOS)
#
# 使用方法:
#   chmod +x install-offline.sh
#   ./install-offline.sh
#
# 作者: Cadence Team
# 版本: v2.1
# 更新记录:
#   v2.1 (2026-08): 移除 cadence-workflow 插件，仅保留 cadence-init
#   v2.0 (2026-04-03): 适配拆分后的双插件 marketplace 结构 (cadence-init + cadence-workflow)
#   v1.0: 初始版本
################################################################################

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印横幅
echo "============================================================"
echo "  Cadence Skills 离线安装脚本 v2.1 (Linux/macOS)"
echo "  包含插件: cadence-init"
echo "============================================================"
echo ""

# 获取脚本所在目录（项目根目录）
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 目标目录
TARGET_DIR="$HOME/.claude/plugins/marketplaces/cadence-skills-local"
MARKETPLACES_DIR="$HOME/.claude/plugins/marketplaces"

echo -e "${BLUE}📁 目标安装目录:${NC} $TARGET_DIR"
echo ""

# 步骤 1: 创建 marketplaces 目录
echo -e "${YELLOW}🔨 步骤 1:${NC} 创建 marketplaces 目录"
if [ ! -d "$MARKETPLACES_DIR" ]; then
    mkdir -p "$MARKETPLACES_DIR"
    echo -e "  ${GREEN}✅ 已创建:${NC} $MARKETPLACES_DIR"
else
    echo -e "  ${BLUE}ℹ️  目录已存在:${NC} $MARKETPLACES_DIR"
fi
echo ""

# 步骤 2: 创建目标目录
echo -e "${YELLOW}🔨 步骤 2:${NC} 创建安装目录"
if [ ! -d "$TARGET_DIR" ]; then
    mkdir -p "$TARGET_DIR"
    echo -e "  ${GREEN}✅ 已创建:${NC} $TARGET_DIR"
else
    echo -e "  ${BLUE}ℹ️  目录已存在:${NC} $TARGET_DIR"
    echo -e "  ${YELLOW}⚠️  将覆盖现有安装${NC}"
fi
echo ""

# 步骤 3: 复制项目文件
echo -e "${YELLOW}🔨 步骤 3:${NC} 复制项目文件"
echo -e "  📂 源目录: $SOURCE_DIR"
echo -e "  📂 目标目录: $TARGET_DIR"
echo ""

if command -v rsync &> /dev/null; then
    echo -e "  ${BLUE}使用 rsync 复制文件...${NC}"
    rsync -av --delete \
        --exclude='.git' \
        --exclude='install-offline.sh' \
        --exclude='install-offline.bat' \
        "$SOURCE_DIR/" "$TARGET_DIR/"
else
    echo -e "  ${BLUE}使用 cp 复制文件...${NC}"
    # 清理目标目录中已不再提供的旧插件与已删除的文档，避免升级残留
    for stale in "cadence-workflow"; do
        if [ -e "$TARGET_DIR/$stale" ]; then
            rm -rf "$TARGET_DIR/$stale"
            echo -e "  ${YELLOW}⚠️  已清理旧文件:${NC} $stale"
        fi
    done
    # readmes 在 cp -r 下只叠加复制，需显式删除已移除的 workflow 指南
    for stale_doc in \
        "readmes/skills/brainstorming.md" \
        "readmes/skills/cad-load.md" \
        "readmes/skills/checkpoint.md" \
        "readmes/skills/data-cleanup.md" \
        "readmes/skills/data-validation.md" \
        "readmes/skills/exploration-flow.md" \
        "readmes/skills/full-flow.md" \
        "readmes/skills/monitor.md" \
        "readmes/skills/quick-flow.md" \
        "readmes/skills/report.md" \
        "readmes/skills/resume.md" \
        "readmes/skills/status.md" \
        "readmes/skills/using-cadence.md" \
        "readmes/skills/version-migration.md"; do
        if [ -e "$TARGET_DIR/$stale_doc" ]; then
            rm -f "$TARGET_DIR/$stale_doc"
            echo -e "  ${YELLOW}⚠️  已清理旧文件:${NC} $stale_doc"
        fi
    done
    # 复制主要目录和文件
    for item in ".claude-plugin" "cadence-init" "CLAUDE.md" "README.md" "LICENSE" ".mcp.json" "readmes"; do
        if [ -e "$SOURCE_DIR/$item" ]; then
            cp -r "$SOURCE_DIR/$item" "$TARGET_DIR/"
        fi
    done
fi

echo ""
echo -e "  ${GREEN}✅ 复制完成${NC}"
echo ""

# 步骤 4: 配置 known_marketplaces.json
echo -e "${YELLOW}🔨 步骤 4:${NC} 配置 known_marketplaces.json"

PLUGINS_DIR="$HOME/.claude/plugins"
MARKETPLACES_FILE="$PLUGINS_DIR/known_marketplaces.json"

# 创建 plugins 目录（如果不存在）
if [ ! -d "$PLUGINS_DIR" ]; then
    mkdir -p "$PLUGINS_DIR"
    echo -e "  ${GREEN}✅ 已创建:${NC} $PLUGINS_DIR"
fi

# 获取当前时间戳
CURRENT_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%S.000Z")

# 检查文件是否存在
if [ ! -f "$MARKETPLACES_FILE" ]; then
    # 文件不存在，创建新文件
    echo -e "  ${BLUE}ℹ️  文件不存在，创建新文件${NC}"

    cat > "$MARKETPLACES_FILE" << EOF
{
  "cadence-skills-local": {
    "source": {
      "source": "github",
      "repo": "cadence/cadence-skills-local"
    },
    "installLocation": "$TARGET_DIR",
    "lastUpdated": "$CURRENT_TIMESTAMP"
  }
}
EOF

    echo -e "  ${GREEN}✅ 已创建配置文件${NC}"
else
    # 文件存在，检查是否已存在配置
    echo -e "  ${BLUE}ℹ️  文件已存在，检查配置${NC}"

    if grep -q '"cadence-skills-local"' "$MARKETPLACES_FILE"; then
        echo -e "  ${BLUE}ℹ️  cadence-skills-local 配置已存在，跳过更新${NC}"
    else
        # 追加配置
        echo -e "  ${BLUE}ℹ️  添加 cadence-skills-local 配置${NC}"

        TEMP_FILE=$(mktemp)
        LAST_BRACE_LINE=$(grep -n '^}$' "$MARKETPLACES_FILE" | tail -1 | cut -d: -f1)

        if [ -n "$LAST_BRACE_LINE" ]; then
            head -n $((LAST_BRACE_LINE - 1)) "$MARKETPLACES_FILE" > "$TEMP_FILE"

            # 确保前一项以逗号结尾
            SECOND_TO_LAST_LINE=$(head -n $((LAST_BRACE_LINE - 1)) "$MARKETPLACES_FILE" | tail -1)
            if [[ ! "$SECOND_TO_LAST_LINE" =~ ,$ ]]; then
                TEMP_FILE2=$(mktemp)
                sed '$d' "$TEMP_FILE" > "$TEMP_FILE2"
                LAST_ENTRY=$(tail -1 "$TEMP_FILE")
                echo "$LAST_ENTRY," >> "$TEMP_FILE2"
                mv "$TEMP_FILE2" "$TEMP_FILE"
            fi

            cat >> "$TEMP_FILE" << EOF
  "cadence-skills-local": {
    "source": {
      "source": "github",
      "repo": "cadence/cadence-skills-local"
    },
    "installLocation": "$TARGET_DIR",
    "lastUpdated": "$CURRENT_TIMESTAMP"
  }
}
EOF

            mv "$TEMP_FILE" "$MARKETPLACES_FILE"
            echo -e "  ${GREEN}✅ 已添加 cadence-skills-local 配置${NC}"
        else
            echo -e "  ${RED}❌ JSON 格式错误，无法找到结尾${NC}"
            rm -f "$TEMP_FILE"
        fi
    fi
fi

echo ""

# 安装完成
echo "============================================================"
echo -e "  ${GREEN}✅ 安装成功！${NC}"
echo "============================================================"
echo ""
echo -e "📍 安装位置: $TARGET_DIR"
echo ""
echo -e "📦 已安装插件:"
echo "  - cadence-init: 项目初始化 (环境检查、项目分析、规则配置、MCP配置)"
echo ""
echo "💡 提示:"
echo "  - 重启 Claude Code 以加载新安装的插件"
echo "  - 使用 /cadence:* 命令访问 Cadence skills"
echo ""
