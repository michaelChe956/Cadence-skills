FROM docker.io/library/archlinux:latest

# 换国内镜像源
RUN sed -i '1i Server = https://mirrors.ustc.edu.cn/archlinux/$repo/os/$arch' /etc/pacman.d/mirrorlist

# 基础工具
RUN pacman -Syu --noconfirm git nodejs npm python python-pip uv which && \
    pacman -Scc --noconfirm

# 创建测试用户
RUN useradd -m -s /bin/bash tester && \
    echo "tester ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

USER tester
WORKDIR /home/tester

# npm 全局目录（免 sudo）+ 允许 postinstall 脚本
RUN mkdir -p /home/tester/.npm-global && \
    npm config set prefix /home/tester/.npm-global && \
    npm config set allow-scripts=@anthropic-ai/claude-code --location=user

ENV PATH="/home/tester/.npm-global/bin:${PATH}"
