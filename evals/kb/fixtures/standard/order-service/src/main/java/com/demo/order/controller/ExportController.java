package com.demo.order.controller;

import org.springframework.web.bind.annotation.*;

/** 订单导出接口：文件保留 7 天（ExportService.RETENTION_DAYS） */
@RestController
@RequestMapping("/api/order/export")
public class ExportController {

    @PostMapping
    public String export() {
        return "taskId";
    }
}
