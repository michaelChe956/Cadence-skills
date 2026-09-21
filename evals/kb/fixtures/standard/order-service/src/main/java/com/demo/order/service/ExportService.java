package com.demo.order.service;

import org.springframework.stereotype.Service;

/** 订单导出服务：导出文件保留 7 天后清理 */
@Service
public class ExportService {

    /** 导出文件保留期（天）。历史 bug：曾误配 30 天，经修复回归 7 天。 */
    public static final int RETENTION_DAYS = 7;
}
