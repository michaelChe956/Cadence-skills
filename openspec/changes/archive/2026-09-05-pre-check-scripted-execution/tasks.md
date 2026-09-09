## 1. 阶段编排与报告契约

- [x] 1.1 完成五阶段 `base-tools → openspec → superpowers-git → superpowers-links → verify` 的确定性串行编排，并为每阶段输出九字段 `phases[]` 记录及必要的 Git/links 元数据；验证：阶段报告 schema、计时和错误字段测试通过。
- [x] 1.2 保留既有 `steps[]` 与顶层报告兼容字段，统一由脚本生成完整报告；验证：旧字段兼容性与 JSON 合法性测试通过。

## 2. SKILL 三步契约与调用边界

- [x] 2.1 将 SKILL.md 收敛为绝对路径定位、项目根一次调用、读取报告呈现三步，移除模型临场编排诱因并将工具调用上限固定为 5；验证：SKILL 契约/禁用命令扫描和真实验收调用计数通过。

## 3. 阶段动作与冲突语义

- [x] 3.1 固化 OpenSpec 四端投影、Superpowers Git 候选与预算、四层软链及解析后等价判定；验证：缺失投影、Git 候选、Bash 3.2/zsh、软链拓扑 fixture 测试通过。
- [x] 3.2 固化普通冲突 warning/skip 与 `--no-interrupt` 备份→创建→验证链语义，确保恢复链失败才报告 failed；验证：冲突矩阵与失败快返测试通过。

## 4. 性能、幂等与只读复核

- [x] 4.1 固化冷热启动统一 ≤120s 验收线、240s 仅网络熔断及 `INFRA_FAIL` 语义；验证：性能/超时预算断言与真实 pre-check 验收通过。
- [x] 4.2 实现只读 verify、普通模式 partial 续跑、no-interrupt 失败快返及幂等 all-skipped；验证：verify、失败路径、二跑零写入和目标树 diff 测试通过。

## 5. 全量验收与契约归档

- [x] 5.1 以 `precheck-v2` 真实布局基线执行 1:1 守卫、全量 eval 回归并完成 whole-branch 终审；验证：pre-check 测试、集成验收及 `PYTHONPATH=. python3 -m unittest discover -s eval/tests -p 'test_*.py'` 全部通过。

> 以上 8 个工作包已于 2026-09-04~05 实施完成，提交 2572384..60fa485（含两端），经逐任务审查+oracle whole-branch 终审。
