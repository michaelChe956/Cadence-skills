package com.demo.order.mq;

import org.springframework.amqp.rabbit.annotation.Exchange;
import org.springframework.amqp.rabbit.annotation.QueueBinding;
import org.springframework.amqp.rabbit.annotation.Queue;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;

/** 订单事件监听：消费 order.paid 完成后续处理（通知、积分） */
@Component
public class OrderEventListener {

    @RabbitListener(bindings = @QueueBinding(
            value = @Queue(value = "order.paid.queue", durable = "true"),
            exchange = @Exchange(value = OrderEventProducer.EXCHANGE),
            key = OrderEventProducer.ROUTING_KEY))
    public void onOrderPaid(String message) {
        // 支付后处理（fixture 静态样本）
    }
}
