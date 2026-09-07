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

export function getDeletedOrdersReport() {
  return apiRequest('/reports/deleted-orders')
}

export function subscribeEmail(email) {
  return apiRequest('/subscriptions/subscribe', 'POST', { email })
}

export function unsubscribeEmail(email) {
  return apiRequest('/subscriptions/unsubscribe', 'POST', { email })
}
