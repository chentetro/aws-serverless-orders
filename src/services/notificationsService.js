import { apiRequest } from './httpClient'

export function subscribeEmail(email) {
  return apiRequest('/subscriptions/subscribe', 'POST', { email })
}

export function unsubscribeEmail(email) {
  return apiRequest('/subscriptions/unsubscribe', 'POST', { email })
}
