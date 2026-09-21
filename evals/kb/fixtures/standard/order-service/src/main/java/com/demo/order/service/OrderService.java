package com.demo.order.service;

import com.demo.order.entity.OrderEntity;
import com.demo.order.entity.OrderStatus;
import com.demo.order.mapper.OrderMapper;
import com.demo.order.mq.OrderEventProducer;
import org.springframework.stereotype.Service;

/** 订单业务逻辑：状态迁移、事件发布与导出 */
@Service
public class OrderService {

    private final OrderMapper orderMapper;
    private final OrderEventProducer orderEventProducer;

    public OrderService(OrderMapper orderMapper, OrderEventProducer orderEventProducer) {
        this.orderMapper = orderMapper;
        this.orderEventProducer = orderEventProducer;
    }

    /**
     * 订单发货：状态机约束——已取消（CANCELLED）的订单不允许再发货；
     * 只有 PAID 状态可以流转到 SHIPPED。
     */
    public void ship(Long orderId) {
        OrderEntity order = orderMapper.selectById(orderId);
        OrderStatus current = OrderStatus.valueOf(order.getStatus());
        if (current == OrderStatus.CANCELLED) {
            throw new IllegalStateException("已取消订单不可发货");
        }
        if (current != OrderStatus.PAID) {
            throw new IllegalStateException("仅已支付订单可发货");
        }
        orderMapper.updateStatus(orderId, OrderStatus.SHIPPED.name());
    }

    /** 订单支付成功回调：CREATED → PAID，并发布订单已支付事件 */
    public void markPaid(Long orderId) {
        orderMapper.updateStatus(orderId, OrderStatus.PAID.name());
        orderEventProducer.sendOrderPaid(orderId);
    }
}
