<template>
  <div>
    <h2>用户列表</h2>
    <div v-for="u in users" :key="u.userId">{{ u.userName }}（{{ u.mobile }}）</div>
    <button @click="load">查询用户信息</button>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { queryUserBasic } from '../api'
const users = ref([])
const load = async () => { users.value = [await queryUserBasic(1)] }
</script>
