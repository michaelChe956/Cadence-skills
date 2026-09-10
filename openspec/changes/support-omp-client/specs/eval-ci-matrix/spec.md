# eval-ci-matrix Specification(Change A delta)

## ADDED Requirements

### Requirement: Docker 夜测考场必须五端覆盖 omp

Tier-1 夜测考场 MUST 将 oh-my-pi(omp)作为第五端纳入,与既有四端同构:

- 考场容器 MUST 能运行 omp 无头会话(`omp -p`):二进制以 ELF 复制方式进入容器(与 kimi 同模式),凭据以最小集(provider 配置自含凭据文件与用户配置)注入;
- stage1 四命令安装流水线 MUST 对 omp 同跑,omp 端安装效果本身即被验收;
- 既有 P1-P8 全部探针 MUST 对 omp 同跑(夜测矩阵整体五端化,而非仅新增探针);
- 结果透视的端维度 MUST 含 omp(端×探针矩阵、合计行、轮次/均时),omp 基线首轮建立,首轮允许低于四端历史基线且透视可见;
- omp 考场不可用(容器化失败)时 MUST 无阻塞降级为四端矩阵,降级事实 MUST 有机器可读载体:omp 端 run 记录(schema 1.0 JSON)落盘并携带 `degrade` 字段说明原因,透视汇总检测到该字段时在输出中打印降级注记;不得阻塞其余端执行(延续既有端级降级语义)。

依赖注记:omp 在未落地规则桥(Change A 框架部分)的项目上跑规则遵循探针必然大面积失败(omp 遮蔽机制下规则与 L0 全盲),故本能力 MUST 与框架改造同 change 落地或在其后启用 omp 探针。

#### Scenario: omp 列出现在夜测透视

- **WHEN** 五端夜测完成并运行透视汇总
- **THEN** 端×探针矩阵包含 omp 列,P1-P8 各行有 omp 成功率/均时/轮次
- **AND** 基线对比对 omp 列按首轮基线执行

#### Scenario: omp 考场故障不拖垮四端

- **WHEN** omp 容器化或无头会话在夜测中失败
- **THEN** 四端矩阵照常执行并产出透视
- **AND** 透视中 omp 列标注考场降级原因
