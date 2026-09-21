package com.demo.order.entity;

/** 订单状态机：CREATED → PAID → SHIPPED → COMPLETED；任意非终态 → CANCELLED */
public enum OrderStatus {
    CREATED("已创建"),
    PAID("已支付"),
    SHIPPED("已发货"),
    COMPLETED("已完成"),
    CANCELLED("已取消");

    private final String label;

    OrderStatus(String label) {
        this.label = label;
    }
}
