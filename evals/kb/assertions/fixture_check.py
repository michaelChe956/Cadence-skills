"""fixture 完整性检查：按埋点说明逐项校验 F1–F10 埋点文件/字段存在（Tier-0 三件套之一）。"""
import sys
from pathlib import Path
from common import Result

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "standard"

CHECKS = {
    "F1a 对外清单API-user-basic": ("user-input-template/api-scope.md", "API-user-basic"),
    "F1b 诉求行锚定": ("user-input-template/api-scope.md", "GET /api/account/{userId}"),
    "F2 SELECT*断链": ("account-service/src/main/resources/mapper/AccountMapper.xml", "SELECT *"),
    "F3a 状态枚举": ("order-service/src/main/java/com/demo/order/entity/OrderStatus.java", "CANCELLED"),
    "F3b 测试规格": ("order-service/src/test/java/com/demo/order/OrderServiceTest.java", "cancelledOrderCannotShip"),
    "F3c 寄生注释": ("order-service/src/main/java/com/demo/order/service/OrderService.java", "已取消订单不可发货"),
    "F4a EVENT生产": ("order-service/src/main/java/com/demo/order/mq/OrderEventProducer.java", "convertAndSend"),
    "F4b EVENT消费": ("order-service/src/main/java/com/demo/order/mq/OrderEventListener.java", "@RabbitListener"),
    "F4c JOB": ("account-service/src/main/java/com/demo/account/job/ReconcileJob.java", "@Scheduled"),
    "F5a 明文密码": ("account-service/src/main/resources/application.yml", "Pr0d@Acct#2026"),
    "F5b 内部IP": ("account-service/src/main/resources/application.yml", "10.20.31.14"),
    "F6 表注释规则": ("db/init.sql", "余额不可为负"),
    "F7 导出保留期": ("order-service/src/main/java/com/demo/order/service/ExportService.java", "RETENTION_DAYS"),
    "F8 product模板": ("user-input-template/product.md", "产品目的"),
    "F9 变更包": ("change-package-F9/code-change.md", "AccountPage.vue 改写为提示页"),
    "F9b 摘要七行": ("change-package-F9/change-summary.md", "业务知识"),
}

TEMPLATE_FILES = ["base-info.md", "project-scope.md", "data-model-scope.md",
                  "configuration-scope.md", "middleware-scope.md", "api-scope.md", "page-scope.md"]


def main():
    r = Result()
    for name, (rel, needle) in CHECKS.items():
        p = FIX / rel
        r.check(name, p.exists() and needle in p.read_text(encoding="utf-8"), rel)
    r.check("模板七文件", all((FIX / "user-input-template" / f).exists() for f in TEMPLATE_FILES))
    sys.exit(0 if r.report("fixture_check") else 1)


if __name__ == "__main__":
    main()
