import axios from 'axios'
// 统一请求封装：baseURL 走 vite 代理转发到后端网关
const request = axios.create({ baseURL: '/api', timeout: 10000 })
export default request
