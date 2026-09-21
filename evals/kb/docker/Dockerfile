FROM docker.io/library/archlinux:latest

# 国内镜像源
RUN sed -i '1i Server = https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch' /etc/pacman.d/mirrorlist

# 基础工具（kb-eval：无 uv/MCP 预热需求）
RUN pacman -Syu --noconfirm git nodejs npm python python-pip which sudo && \
    pacman -Scc --noconfirm

RUN pip install --break-system-packages pyyaml

# 测试用户
RUN useradd -m -s /bin/bash tester && \
    echo "tester ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER tester
WORKDIR /home/tester

# npm 用户级全局目录（免 sudo 安装 CLI）+ 国内源
RUN mkdir -p /home/tester/.npm-global && \
    npm config set prefix /home/tester/.npm-global && \
    npm config set registry https://registry.npmmirror.com && \
    npm config set allow-scripts=@anthropic-ai/claude-code --location=user

ENV PATH="/home/tester/.npm-global/bin:${PATH}"
