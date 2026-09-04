const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''//קובץ ENV יכיל שם את כתובת הAPI GATEWAY

async function requestNotification(endpoint, email, method = 'POST') {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email }),
  })

  const contentType = response.headers.get('content-type') ?? ''
  const responseBody = contentType.includes('application/json')
    ? await response.json()
    : await response.text()

  if (!response.ok) {
    const message =
      typeof responseBody === 'object' && responseBody?.message
        ? responseBody.message
        : typeof responseBody === 'string' && responseBody
          ? responseBody
          : 'The notification request failed.'

    throw new Error(message)
  }

  return responseBody
}

export function subscribeToNotifications(email) {
  return requestNotification('/api/notifications/subscribe', email, 'POST')//מחליפה את הנתיב שהגדרתי בAPI GATEWAY שקשור לSUBSCRIBE
}

export function unsubscribeFromNotifications(email) {
  return requestNotification('/api/notifications/unsubscribe', email, 'DELETE')//מחליפה את הנתיב שהגדרתי בAPI GATEWAY לUNSUBSCRIBE
}
