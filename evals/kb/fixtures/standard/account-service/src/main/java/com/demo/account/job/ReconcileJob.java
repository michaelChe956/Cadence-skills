package com.demo.account.job;

import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;

/**
 * 每日账户对账定时任务。
 * 启用证据：@Scheduled 注解 + application.yml 的 reconcile.enabled=true；
 * 重试次数取 reconcile.retry-times 配置。
 */
@Component
public class ReconcileJob {

    @Scheduled(cron = "0 0 2 * * ?")
    public void reconcile() {
        // 对账逻辑（fixture 静态样本：实现省略，语义与启用证据见类注释与配置）
    }
}
