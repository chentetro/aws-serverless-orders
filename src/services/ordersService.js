import { apiRequest } from './httpClient'

export function getOrders() {
  return apiRequest('/api/orders')
}

export function createOrder(orderData) {
  return apiRequest('/api/orders', 'POST', orderData)
}

export function deleteOrder(orderId) {
  return apiRequest(`/api/orders/${orderId}`, 'DELETE')
}
