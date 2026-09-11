# cadence devbox Windows 首次安装脚本（设计 4.6：≤5 步；无 WSL2/OAuth 表述）
# 用法（发布包解压后，devbox\ 目录旁打开 PowerShell）：
#   powershell -ExecutionPolicy Bypass -File .\devbox\install.ps1 -Workspace D:\code
param(
  [string]$InstallDir = "",
  [string]$Workspace = "",
  [string]$Image = "cadence-devbox:1.0.0"
)
$ErrorActionPreference = 'Stop'
if (-not $InstallDir) { $InstallDir = Join-Path (Split-Path $PSScriptRoot -Parent) 'cadence-box' }

function Info($m) { Write-Host "[cadence] $m" -ForegroundColor Cyan }
function Warn($m) { Write-Host "[cadence][警告] $m" -ForegroundColor Yellow }
function Die($m)  { Write-Host "[cadence][错误] $m" -ForegroundColor Red; exit 1 }

# ---- 第 1 步：检测 Docker Desktop ----
Info '第 1/5 步：检测 Docker Desktop'
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  Die "未检测到 docker。请先安装 Docker Desktop（安装中可能提示开启主板虚拟化并重启一次）：https://www.docker.com/products/docker-desktop/ ；安装完成并启动后重新运行本脚本。"
}
Info "docker 已就绪：$(docker --version)"

# ---- 第 2 步：生成 cadence-box.yaml 与 stack 目录 ----
Info "第 2/5 步：生成安装目录 $InstallDir"
if (-not $Workspace) {
  $Workspace = Read-Host '请输入宿主代码父目录绝对路径（例如 D:\code，将挂载为容器内 /workspace）'
}
if (-not (Test-Path $Workspace)) { Die "目录不存在：$Workspace" }
New-Item -ItemType Directory -Force -Path "$InstallDir\stack" | Out-Null
Copy-Item "$PSScriptRoot\compose.yaml" "$InstallDir\stack\compose.yaml" -Force
Copy-Item "$PSScriptRoot\stack\docker-compose.no-sock.yml" "$InstallDir\stack\docker-compose.no-sock.yml" -Force
if (Test-Path "$InstallDir\stack\catalog") { Remove-Item "$InstallDir\stack\catalog" -Recurse -Force }
Copy-Item "$PSScriptRoot\stack\catalog" "$InstallDir\stack\catalog" -Recurse -Force
if (Test-Path "$InstallDir\cadence-box.yaml") {
  Warn "cadence-box.yaml 已存在，保留不覆盖（如需重新生成请先改名备份）"
} else {
  Copy-Item "$PSScriptRoot\cadence-box.yaml.example" "$InstallDir\cadence-box.yaml"
  Warn "已生成 cadence-box.yaml 模板——该文件=密钥，勿提交勿分享"
}
# .env：工作区与镜像与启用 profile（默认空=仅 mysql+redis）
$ws = ($Workspace -replace '\\', '/').TrimEnd('/')
"CADENCE_WORKSPACE=$ws`nCADENCE_DEVBOX_IMAGE=$Image`nCOMPOSE_PROFILES=" | Set-Content "$InstallDir\stack\.env" -Encoding ascii
# 本地 .gitignore（安装目录不是 git 仓库时亦预留）
"cadence-box.yaml`nstack/.env`nstack/CHANGES.md`nstack/data/`n" | Set-Content "$InstallDir\.gitignore" -Encoding ascii
Info "请编辑 $InstallDir\cadence-box.yaml 填写 provider 端点/key/模型（git.name/email 也要填）"
$done = Read-Host '填完后按回车继续（Ctrl+C 退出先去填）'

# ---- 第 3 步：daemon.json 写 registry-mirrors（国内拉取兜底，设计 4.7） ----
Info '第 3/5 步：配置 Docker 镜像加速（daemon.json）'
$daemonPath = Join-Path $env:ProgramData 'Docker\config\daemon.json'
$mirrors = @('https://docker.m.daocloud.io', 'https://docker.1ms.run')
New-Item -ItemType Directory -Force -Path (Split-Path $daemonPath) | Out-Null
$obj = [ordered]@{}
$changed = $false
if (Test-Path $daemonPath) {
  Copy-Item $daemonPath "$daemonPath.bak-$(Get-Date -Format yyyyMMdd-HHmmss)"
  try {
    $old = Get-Content $daemonPath -Raw | ConvertFrom-Json
    foreach ($p in $old.PSObject.Properties) { $obj[$p.Name] = $p.Value }
  } catch { Warn "现有 daemon.json 解析失败，将只保留 registry-mirrors（原文件已备份）" }
}
$existing = @($obj['registry-mirrors'])
$merged = @($existing + $mirrors | Where-Object { $_ } | Select-Object -Unique)
if (-not $existing -or ($merged -join ',') -ne ($existing -join ',')) {
  $obj['registry-mirrors'] = $merged
  $obj | ConvertTo-Json -Depth 10 | Set-Content $daemonPath -Encoding ascii
  $changed = $true
}
if ($changed) {
  Warn '已写入 registry-mirrors，需要重启 Docker Desktop 生效：右下角 Docker 图标 -> Quit Docker Desktop -> 重新启动'
  $null = Read-Host '重启完成后按回车继续'
  $ErrorActionPreference = 'Continue'
  docker info 2>$null | Out-Null
  $okDocker = ($LASTEXITCODE -eq 0)
  $ErrorActionPreference = 'Stop'
  if (-not $okDocker) { Die 'docker 不可用：请确认 Docker Desktop 已完全启动后重试（可直接重跑本脚本，已生成内容幂等保留）' }
} else { Info 'registry-mirrors 已配置，跳过' }

# ---- 第 4 步：预创建外部卷 + 拉镜像 + up -d ----
Info '第 4/5 步：创建数据卷并启动'
$vols = @('cadence-claude','cadence-codex','cadence-pi','cadence-kimi','cadence-agents','cadence-omp',
          'cadence-m2','cadence-npm','cadence-npm-global','cadence-uv','cadence-pip','cadence-gradle',
          'cadence-mysql-data','cadence-redis-data','cadence-rabbitmq-data','cadence-minio-data')
foreach ($v in $vols) { docker volume create $v | Out-Null }
$ErrorActionPreference = 'Continue'
docker image inspect $Image 2>$null | Out-Null
$haveImage = ($LASTEXITCODE -eq 0)
$ErrorActionPreference = 'Stop'
if (-not $haveImage) {
  Info "拉取镜像 $Image ……"
  docker pull $Image
  if ($LASTEXITCODE -ne 0) {
    Warn "拉取失败：请确认 Docker Desktop 已重启（镜像加速生效）；离线场景可用维护者提供的 tar 包：docker load -i cadence-devbox.tar 后重跑"
    Die '镜像不可用，终止（安装目录内容已就绪，重跑本脚本幂等）'
  }
}
docker compose --project-directory "$InstallDir\stack" -f "$InstallDir\stack\compose.yaml" up -d
if ($LASTEXITCODE -ne 0) { Die 'compose up 失败：请把上方错误反馈维护者' }

# ---- 第 5 步：后续提示 ----
Info '第 5/5 步：完成。后续操作：'
Write-Host @"
  1. 进入容器：docker compose -f "$InstallDir\stack\compose.yaml" exec devbox bash
     （VS Code 亦可：安装 Dev Containers 扩展后 Attach to Running Container）
  2. 容器内验证鉴权：执行 claude 发一条消息（五端：claude/codex/pi/kimi/omp）
  3. 你的全部仓库在容器内 /workspace 下，与 Windows 双向同步
  4. 换 key/换模型：改 $InstallDir\cadence-box.yaml →
     docker compose -f "$InstallDir\stack\compose.yaml" restart devbox
  5. 加开中间件（容器内）：stack enable mq   # rabbitmq；stack enable storage  # minio
"@
Info '安装完成。'
