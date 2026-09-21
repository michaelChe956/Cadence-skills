<template>
  <div>
    <h2>账户查询</h2>
    <div v-if="acct">账户号：{{ acct.accountNo }} 余额：{{ acct.balance }}</div>
    <button @click="load">查询账户</button>
  </div>
</template>
<script setup>
import { ref } from 'vue'
import { queryAccount } from '../api'
const acct = ref(null)
const load = async () => { acct.value = await queryAccount(1) }
</script>
