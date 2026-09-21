# 代码变更

- MR：本地模拟（无平台 MR）
- 源分支：{{BRANCH}}，目标分支：{{BRANCH}}
- 起始提交：F9_BASE，结束提交：F9_HEAD（runner apply-f9 替换为实际值）
- 修改工程：account-service、web-portal
- 修改文件与符号：删除 AccountController.java、删除 AccountService.java、AccountPage.vue 改写为提示页、api/index.js 移除 queryAccount 导出行
- 代码变更说明：下线账户查询端点、服务层与前端调用（页面保留并改为提示页，路由不悬空）
- 本地可验证范围：git diff 与文件级核对
