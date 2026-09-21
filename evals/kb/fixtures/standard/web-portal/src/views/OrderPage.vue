<template>
  <div>
    <h2>订单管理</h2>
    <button @click="ship">发货</button>
    <button @click="exportAll">导出订单</button>
  </div>
</template>
<script setup>
import { shipOrder, exportOrder } from '../api'
const ship = async () => { await shipOrder(1) }
const exportAll = async () => { await exportOrder() }
</script>
