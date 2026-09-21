package com.demo.order.entity;

/** 订单实体（对应 t_order） */
public class OrderEntity {
    private Long orderId;
    /** 下单用户 ID，与 t_user.user_id 同源 */
    private Long userId;
    /** 订单状态，取值见 OrderStatus 枚举 */
    private String status;
    private java.math.BigDecimal amount;
    // fixture 静态样本：标准 getter/setter 略
}
