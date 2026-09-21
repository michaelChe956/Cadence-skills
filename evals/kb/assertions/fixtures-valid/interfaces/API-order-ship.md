# 订单发货

POST /api/order/{orderId}/ship。业务规则（寄生原文）：已取消订单不可发货；仅已支付订单可发货。
