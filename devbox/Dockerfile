# syntax=docker/dockerfile:1
# devbox 镜像——分层与更新策略见设计 4.1；构建上下文 = devbox/
# 版本 pin 唯一来源 = devbox/versions.env（T9 构建命令注入 --build-arg；此处默认值 MUST 与之同步）

# ============================== L1 os（季/年重建） ==============================
FROM ubuntu:24.04

ARG JDK_VERSION=21
ARG MAVEN_VERSION=3.9.16
ARG NODE_VERSION=24.21.0
ARG UV_VERSION=0.12.11
ARG PYYAML_VERSION=6.0.3
ARG CLAUDE_CODE_VERSION=2.1.247
ARG CODEX_VERSION=0.153.4
ARG PI_VERSION=0.85.0
ARG OMP_VERSION=18.1.17
ARG BUN_VERSION=1.4.2
ARG KIMI_INSTALL_URL=https://code.kimi.com/kimi-code/install.sh
ARG ADOPTIUM_KEY_URL=https://packages.adoptium.net/artifactory/api/gpg/key/public
# RUN 默认 shell 为 dash（无 pipefail）——curl 管道断链会静默成功，统一切 bash+pipefail。
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

ENV DEBIAN_FRONTEND=noninteractive
# apt：aliyun 源
RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.aliyun.com@; s@//.*security.ubuntu.com@//mirrors.aliyun.com@' /etc/apt/sources.list.d/ubuntu.sources \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      git curl ripgrep vim tmux sudo less procps net-tools openssh-client jq ca-certificates \
      gnupg unzip xz-utils tzdata mysql-client redis-tools python3 python3-pip \
 && rm -rf /var/lib/apt/lists/*
# docker-ce-cli + compose 插件（aliyun docker-ce 源）
RUN install -d -m 0755 /etc/apt/keyrings \
 && curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc \
 && printf 'deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://mirrors.aliyun.com/docker-ce/linux/ubuntu noble stable\n' > /etc/apt/sources.list.d/docker.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends docker-ce-cli docker-compose-plugin \
 && rm -rf /var/lib/apt/lists/*
# 非 root dev（uid 1000）；免密 sudo——docker.sock 挂载等同宿主 root。
RUN userdel --remove ubuntu 2>/dev/null || true \
 && useradd -m -s /bin/bash -u 1000 dev \
 && printf 'dev ALL=(ALL) NOPASSWD:ALL\n' > /etc/sudoers.d/dev \
 && chmod 440 /etc/sudoers.d/dev

# ============================== L2 runtime（季更，ARG pin） ==============================
# JDK：Temurin（USTC adoptium deb 源；密钥经上游 URL 获取）
RUN install -d -m 0755 /etc/apt/keyrings \
 && curl -fsSL "$ADOPTIUM_KEY_URL" | gpg --dearmor -o /etc/apt/keyrings/adoptium.gpg \
 && printf 'deb [signed-by=/etc/apt/keyrings/adoptium.gpg] https://mirrors.ustc.edu.cn/adoptium/deb noble main\n' > /etc/apt/sources.list.d/adoptium.list \
 && apt-get update \
 && apt-get install -y --no-install-recommends "temurin-${JDK_VERSION}-jdk" \
 && rm -rf "/usr/lib/jvm/temurin-${JDK_VERSION}-jdk-amd64/jmods" \
           "/usr/lib/jvm/temurin-${JDK_VERSION}-jdk-amd64/lib/src.zip" \
           "/usr/lib/jvm/temurin-${JDK_VERSION}-jdk-amd64/man" \
 && rm -rf /var/lib/apt/lists/*
# Maven：aliyun tarball（2026-09-11 实测：USTC/TUNA 对容器 TLS 指纹 GET 误杀 403；aliyun/腾讯 200）
RUN curl -fsSL "https://mirrors.aliyun.com/apache/maven/maven-3/${MAVEN_VERSION}/binaries/apache-maven-${MAVEN_VERSION}-bin.tar.gz" -o /tmp/maven.tgz \
 && tar -xzf /tmp/maven.tgz -C /opt \
 && ln -sf "/opt/apache-maven-${MAVEN_VERSION}/bin/mvn" /usr/local/bin/mvn \
 && rm -f /tmp/maven.tgz
# Node：npmmirror tarball
RUN curl -fsSL "https://cdn.npmmirror.com/binaries/node/v${NODE_VERSION}/node-v${NODE_VERSION}-linux-x64.tar.xz" -o /tmp/node.tar.xz \
 && tar -xJf /tmp/node.tar.xz -C /opt \
 && ln -sf "/opt/node-v${NODE_VERSION}-linux-x64/bin/node" /usr/local/bin/node \
 && ln -sf "/opt/node-v${NODE_VERSION}-linux-x64/bin/npm" /usr/local/bin/npm \
 && ln -sf "/opt/node-v${NODE_VERSION}-linux-x64/bin/npx" /usr/local/bin/npx \
 && rm -f /tmp/node.tar.xz
# uv + PyYAML（aliyun pypi；render-auth.py 依赖）
RUN pip3 install --break-system-packages --no-cache-dir \
      --index-url https://mirrors.aliyun.com/pypi/simple/ \
      "uv==${UV_VERSION}" "PyYAML==${PYYAML_VERSION}"

# ============================== L3 agents（周更重建 + 容器内自更新） ==============================
# npm 系四端 + bun 运行时（omp 她bang 需要）：root 装入 /usr/local——不被 ~/.npm-global 空卷遮蔽；层内清 npm 缓存。
# 2026-09-11 实测：omp 官方安装器走 GitHub releases/bun.sh，构建网络不可达；npm 包 @oh-my-pi/pi-coding-agent 与 bun 均在 npmmirror，改走 npm（版本 pin 见 versions.env）。
# 注意 prefix：node 为 /opt tarball 安装，npm 默认全局 prefix 会解析到 /opt/node-*/（PATH 外）——必须显式 set prefix /usr/local。
# --omit=optional：omp 的 optionalDependencies（sherpa-onnx-node 本地语音、@huggingface/transformers）数百 MB，非核心功能，砍。
RUN npm config set registry https://registry.npmmirror.com \
 && npm config set prefix /usr/local \
 && npm install -g --omit=optional \
      "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
      "@openai/codex@${CODEX_VERSION}" \
      "@earendil-works/pi-coding-agent@${PI_VERSION}" \
      "bun@${BUN_VERSION}" \
      "@oh-my-pi/pi-coding-agent@${OMP_VERSION}" \
 && npm cache clean --force \
 && rm -rf /usr/local/lib/node_modules/@oh-my-pi/pi-coding-agent/node_modules/onnxruntime-node \
           /usr/local/lib/node_modules/@oh-my-pi/pi-coding-agent/node_modules/sherpa-onnx-* \
 && ls /usr/local/bin/ | grep -E '^(claude|codex|pi|omp|bun)$' \
 && rm -f /root/.npmrc
# kimi（月之光自有 CDN）；omp 已并入上方 npm 批次
ENV HOME=/home/dev
USER dev
RUN curl -fsSL "$KIMI_INSTALL_URL" | bash
ENV PATH="/home/dev/.npm-global/bin:/home/dev/.local/bin:/home/dev/.kimi-code/bin:${PATH}" \
    CHOKIDAR_USEPOLLING=1
# dev 运行期：npm 前缀落卷；pip/uv 国内源固化（不被卷遮蔽）
RUN mkdir -p /home/dev/.npm-global /home/dev/.config/pip /home/dev/.config/uv \
 && printf 'registry=https://registry.npmmirror.com\nprefix=/home/dev/.npm-global\n' > /home/dev/.npmrc \
 && printf '[global]\nindex-url = https://mirrors.aliyun.com/pypi/simple/\n' > /home/dev/.config/pip/pip.conf \
 && printf '[[index]]\nurl = "https://mirrors.aliyun.com/pypi/simple/"\ndefault = true\n' > /home/dev/.config/uv/uv.toml
# ============================== 镜像内固定布局（Contract 4） ==============================
USER root
COPY --chmod=0755 render-auth.py /usr/local/lib/cadence/render-auth.py
COPY --chmod=0755 stack/stack-lib.sh /usr/local/lib/cadence/stack-lib.sh
COPY --chmod=0755 stack/stack.sh /usr/local/bin/stack
COPY --chmod=0755 entrypoint.sh /usr/local/bin/cadence-entrypoint
COPY compose.yaml /opt/cadence/stack/compose.yaml
COPY stack/docker-compose.no-sock.yml /opt/cadence/stack/docker-compose.no-sock.yml
COPY stack/catalog/ /opt/cadence/stack/catalog/
RUN printf 'jdk=temurin-%s\nmaven=%s\nnode=%s\nuv=%s\npyyaml=%s\nclaude-code=%s\ncodex=%s\npi=%s\nkimi=installer\nomp=%s\nbun=%s\nbuilt=%s\n' \
      "$JDK_VERSION" "$MAVEN_VERSION" "$NODE_VERSION" "$UV_VERSION" "$PYYAML_VERSION" \
      "$CLAUDE_CODE_VERSION" "$CODEX_VERSION" "$PI_VERSION" "$OMP_VERSION" "$BUN_VERSION" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
      > /opt/cadence/versions.txt
USER dev
WORKDIR /workspace
ENTRYPOINT ["/usr/local/bin/cadence-entrypoint"]
CMD ["sleep", "infinity"]
