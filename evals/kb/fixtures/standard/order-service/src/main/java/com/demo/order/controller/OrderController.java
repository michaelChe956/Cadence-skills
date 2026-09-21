package com.demo.order.controller;

import com.demo.order.service.OrderService;
import org.springframework.web.bind.annotation.*;

/** 订单接口：状态流转由 OrderService 状态机约束（已取消订单不可发货） */
@RestController
@RequestMapping("/api/order")
public class OrderController {

    private final OrderService orderService;

    public OrderController(OrderService orderService) {
        this.orderService = orderService;
    }

    @PostMapping("/{orderId}/ship")
    public String ship(@PathVariable("orderId") Long orderId) {
        orderService.ship(orderId);
        return "ok";
    }
}
