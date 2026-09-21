package com.demo.order;

import com.demo.order.entity.OrderEntity;
import com.demo.order.entity.OrderStatus;
import com.demo.order.mapper.OrderMapper;
import com.demo.order.mq.OrderEventProducer;
import com.demo.order.service.OrderService;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** 订单状态机行为规格（测试即规格） */
class OrderServiceTest {

    /** 业务规则：已取消订单不可发货（桩返回 CANCELLED 订单） */
    @Test
    void cancelledOrderCannotShip() {
        OrderMapper stub = new OrderMapper() {
            @Override public OrderEntity selectById(Long id) {
                OrderEntity o = new OrderEntity();
                o.setOrderId(id);
                o.setStatus(OrderStatus.CANCELLED.name());
                return o;
            }
            @Override public int updateStatus(Long id, String status) { return 1; }
        };
        OrderService service = new OrderService(stub, new OrderEventProducer(null));
        assertThrows(IllegalStateException.class, () -> service.ship(1L));
    }
}
