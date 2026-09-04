import { apiRequest } from './httpClient'

export function subscribeToNotifications(email) {
  return apiRequest('/api/notifications/subscribe', 'POST', { email })
}

export function unsubscribeFromNotifications(email) {
  return apiRequest('/api/notifications/unsubscribe', 'DELETE', { email })
}
