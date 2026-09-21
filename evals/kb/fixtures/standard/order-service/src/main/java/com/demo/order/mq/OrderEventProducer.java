package com.demo.order.mq;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;

/** 订单事件生产者：订单支付成功后发送 order.paid 事件 */
@Component
public class OrderEventProducer {

    public static final String EXCHANGE = "order.exchange";
    public static final String ROUTING_KEY = "order.paid";

    private final RabbitTemplate rabbitTemplate;

    public OrderEventProducer(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public void sendOrderPaid(Long orderId) {
        rabbitTemplate.convertAndSend(EXCHANGE, ROUTING_KEY, "{\"orderId\":" + orderId + "}");
    }
}
