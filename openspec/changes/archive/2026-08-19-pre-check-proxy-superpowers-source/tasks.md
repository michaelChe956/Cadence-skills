# Tasks: pre-check-proxy-superpowers-source

## 1. 镜像与报告
- [x] 1.1 cn.sh：CADENCE_SUPERPOWERS_GIT 改为三代理候选（空格分隔）
- [x] 1.2 pre-check.sh：hints 输出改 `superpowers_git_candidates` JSON 数组（default 单元素）

## 2. SKILL.md 步骤 6 重写
- [x] 2.1 clone 模板：候选循环 + `--depth 1`，全败报 failed
- [x] 2.2 更新模板：origin 非候选时切换后更新
- [x] 2.3 删除离线安装方式与降级描述；失败语义收紧为报错

## 3. 测试与验证
- [x] 3.1 test.sh：断言改候选数组（cn=3 个 gh 代理、default=github 单元素）
- [x] 3.2 test.sh 全量通过；人工验证一次 cn 模式报告 JSON 结构
