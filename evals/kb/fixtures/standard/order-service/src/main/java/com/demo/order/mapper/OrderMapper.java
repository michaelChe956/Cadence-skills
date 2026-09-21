package com.demo.order.mapper;

import com.demo.order.entity.OrderEntity;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/** t_order 表数据访问 */
@Mapper
public interface OrderMapper {
    OrderEntity selectById(@Param("orderId") Long orderId);
    int updateStatus(@Param("orderId") Long orderId, @Param("status") String status);
}
