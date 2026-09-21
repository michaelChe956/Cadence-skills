import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import UserList from './views/UserList.vue'
import OrderPage from './views/OrderPage.vue'
import AccountPage from './views/AccountPage.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/users', component: UserList },
    { path: '/orders', component: OrderPage },
    { path: '/accounts', component: AccountPage }
  ]
})
createApp(App).use(router).mount('#app')
