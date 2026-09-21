import request from './request'
export const queryUserBasic = (userId) => request.get(`/user/basic/${userId}`)
export const queryAccount = (userId) => request.get(`/account/${userId}`)
export const shipOrder = (orderId) => request.post(`/order/${orderId}/ship`)
export const exportOrder = () => request.post('/order/export')
