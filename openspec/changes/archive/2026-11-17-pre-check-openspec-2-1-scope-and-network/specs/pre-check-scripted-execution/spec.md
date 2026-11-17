# pre-check-scripted-execution 规格增量

## ADDED Requirements

### Requirement: OpenSpec 作用域与初始化参数

pre-check MUST 在为缺失客户端执行 OpenSpec 初始化前探测 CLI 版本。CLI 版本 ≥ 2.1.0 时，MUST 为初始化调用显式指定项目作用域，使技能写入项目根的共享技能目录；CLI 版本低于 2.1.0 时，MUST NOT 传入该参数，保持既有调用形态。CLI 版本无法解析时 MUST 按低于 2.1.0 处理。四端投影复核失败时，对应 phase 的 `error` MUST 保留既有失败前缀，并在 CLI ≥ 2.1.0 时追加说明该版本默认把技能装入用户家目录的全局作用域，以及在项目根重跑初始化的补救方向。

#### Scenario: 2.1.0 在无既有投影的项目上产出项目根投影

- **WHEN** 项目内没有任何既有 OpenSpec 技能投影，且 CLI 版本为 2.1.0
- **THEN** 初始化调用带项目作用域参数，共享技能写入项目根的共享技能目录并登记已配置客户端，用户家目录下不出现任何 OpenSpec 技能目录，四端复核通过且 phase 结果为 `success`

#### Scenario: 旧版本 CLI 不接受作用域参数

- **WHEN** CLI 版本为 2.0.0 或更早
- **THEN** 初始化调用不携带作用域参数，既有调用形态与既有判定口径不变

#### Scenario: 复核失败文案点名作用域原因

- **WHEN** CLI 版本 ≥ 2.1.0 且四端投影复核失败
- **THEN** phase 的 `error` 以既有失败前缀开头，并写明该版本默认装入家目录全局作用域的原因与补救方向

### Requirement: OpenSpec 网络调用超时与镜像回退

OpenSpec CLI ≥ 2.1.0 的初始化与更新需要访问 GitHub 获取技能，而 CLI 自身不提供网络超时。pre-check MUST 对该版本的初始化与更新施加单次调用超时与阶段级网络预算，MUST 使二者在同一阶段内共享同一截止时间，MUST NOT 通过重复重试使整体运行突破仓库规定的网络熔断上限。单次调用超时 MUST 不超过 60 秒，阶段级网络预算 MUST 不超过 180 秒，两者 MUST 可由环境变量调整。超时 MUST 按失败报告，对应 phase 的 `error` MUST 写明已尝试次数与下一步。CLI 低于 2.1.0 时，MUST NOT 施加该超时，保持既有调用形态。

`--mirror cn` 时，pre-check MUST 按镜像配置给出的 GitHub 加速代理候选顺序访问 GitHub，前一个候选失败时方可尝试下一个。MUST 通过仅作用于该次命令子进程的 git url 重写实现，MUST NOT 写入任何 git 全局或仓库配置，MUST NOT 改写用户已有的同类环境配置。默认镜像 MUST 直连，不启用代理。

#### Scenario: GitHub 不可达时有界失败

- **WHEN** CLI 版本 ≥ 2.1.0 且 GitHub 在超时窗口内始终不可达
- **THEN** 阶段以失败结束并写明超时、已尝试次数与下一步，整个运行不会因该调用无限挂起

#### Scenario: 加速代理逐个回退

- **WHEN** `--mirror cn` 下第一个加速代理候选访问失败而第二个可用
- **THEN** 脚本依次尝试候选并在可用候选上成功完成调用，报告不出现失败

#### Scenario: 代理改写只作用于本次调用

- **WHEN** 脚本经加速代理完成 OpenSpec 调用
- **THEN** 重写仅出现在该次命令的子进程环境中，git 配置与用户既有环境配置保持不变

### Requirement: 升级范围与镜像透传

`--upgrade` 的升级范围 MUST 包含 ast-grep、codegraph、openspec、pi-mcp-adapter 与 uv 本体，MUST NOT 包含 uvx 临时包与 playwright-cli。pi-mcp-adapter MUST 经其自身的更新机制升级，MUST 沿用当前镜像的 npm 源，MUST NOT 直接改写其安装目录；版本低于当前源 latest 时 MUST 升级并记录版本变化，已是最新时 MUST NOT 触发更新动作，版本固定写法 MUST 视为用户的有意选择并保持不变，升级后版本未追到 latest MUST 记为升级失败。

安装 pi-mcp-adapter 与获取 codegraph 外网回退下载时 MUST 跟随当前镜像；codegraph 在大陆镜像下 MUST 经 GitHub 加速代理获取回退下载，用户已自行设置下载源时 MUST NOT 覆盖。pre-check MUST NOT 执行 codegraph 的初始化、索引或同步。

#### Scenario: 落后版本被升级并记录版本变化

- **WHEN** `--upgrade` 下 pi-mcp-adapter 的已装版本低于当前源 latest
- **THEN** 脚本通过 pi 的更新机制完成升级，报告该工具的版本由旧值变为新值，且升级调用使用当前镜像的 npm 源

#### Scenario: 已是最新与固定版本不触发更新

- **WHEN** pi-mcp-adapter 已是当前源 latest，或其包名带固定版本写法
- **THEN** 脚本不发起更新动作，对应步骤保持既有状态

#### Scenario: 升级未达 latest 记为失败

- **WHEN** 更新动作执行后已装版本仍未追到 latest
- **THEN** 对应步骤记为升级失败并带上目标版本与当前版本，整体结果按既有失败语义判定

#### Scenario: 脚本不重建 codegraph 索引

- **WHEN** pre-check 完成工具检查与升级
- **THEN** 脚本不执行 codegraph 的初始化、索引或同步，索引由后续阶段决定
