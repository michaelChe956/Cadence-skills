# eval-ci-matrix Specification(Change B delta)

## ADDED Requirements

### Requirement: Docker 夜测评分必须消费探针断言 spec

Docker 夜测(`eval/docker/night.py`)的探针评分 MUST 消费探针定义中的 `assertions` 列表:对 `text_contains`/`text_lacks` 逐条以最终输出文本判定;既有 P 组探针的既有评分语义 MUST NOT 改变。探针定义含断言而无分支时 MUST NOT 默认 PASS——不存在「无条件通过」路径(防假绿)。

#### Scenario: 断言不满足判 FAIL

- **WHEN** R1 探针输出不含任何索引锚点
- **THEN** 该探针判定 FAIL 而非 PASS

### Requirement: stage1 确定性断言必须落盘为夜测记录并入透视

stage1 确定性断言结果 MUST 以 schema 1.0 run 记录落盘(如 `probe_id="stage1"`),任一断言失败 MUST 使该记录为 FAIL 并出现在透视矩阵;不得只存在于 stdout。

#### Scenario: stage1 断言失败进入透视

- **WHEN** 测试项目缺一个应有软链且夜测完成
- **THEN** 透视矩阵出现 stage1 行的 FAIL 条目,可定位到 `omp.symlinks`
