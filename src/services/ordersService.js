import { apiRequest } from './httpClient'

export function getOrders() {
  return apiRequest('/orders')
}

export function createOrder(orderData) {
  return apiRequest('/orders', 'POST', orderData)
}

export function getOrder(orderId) {
  return apiRequest(`/orders/${orderId}`)
}

export function updateOrder(orderId, orderData) {
  return apiRequest(`/orders/${orderId}`, 'PUT', orderData)
}

export function deleteOrder(orderId) {
  return apiRequest(`/orders/${orderId}`, 'DELETE')
}
