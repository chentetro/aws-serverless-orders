import { apiRequest } from './httpClient'

export function getOrders() {
  return apiRequest('/orders')
}

export function createOrder(orderData) {
  return apiRequest('/orders', 'POST', orderData)
}

export function extractOrderFromDocument({ imageBase64, fileName }) {
  return apiRequest('/orders/extract', 'POST', { imageBase64, fileName })
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

function parseReportNumber(value) {
  const parsedValue = Number(value)
  return Number.isFinite(parsedValue) ? parsedValue : 0
}

export async function getDeletedOrdersReport() {
  const response = await apiRequest('/reports/deleted-orders')

  if (response === null || typeof response !== 'object' || Array.isArray(response)) {
    throw new Error('The deleted orders report returned an invalid response.')
  }

  return {
    totalDeletedOrders: parseReportNumber(response.totalDeletedOrders),
    totalLostRevenue: parseReportNumber(response.totalLostRevenue),
    orders: Array.isArray(response.orders) ? response.orders : [],
    pdfUrl: response.url ?? response.pdfUrl ?? response.downloadUrl ?? null,
  }
}

export function subscribeEmail(email) {
  return apiRequest('/subscriptions/subscribe', 'POST', { email })
}

export function unsubscribeEmail(email) {
  return apiRequest('/subscriptions/unsubscribe', 'POST', { email })
}
