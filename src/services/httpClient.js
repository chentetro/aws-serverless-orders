const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

async function parseResponse(response) {
  const contentType = response.headers.get('content-type') ?? ''

  if (contentType.includes('application/json')) {
    const responseText = await response.text()

    if (!responseText) {
      return null
    }

    try {
      return JSON.parse(responseText)
    } catch {
      return responseText
    }
  }

  return response.text()
}

function getErrorMessage(responseBody) {
  if (typeof responseBody === 'object' && responseBody !== null) {
    return responseBody.message || responseBody.error || 'The API request failed.'
  }

  return typeof responseBody === 'string' && responseBody
    ? responseBody
    : 'The API request failed.'
}

export async function apiRequest(endpoint, method = 'GET', data = null) {
  const requestOptions = { method }

  if (data !== null && data !== undefined) {
    requestOptions.headers = {
      'Content-Type': 'application/json',
    }
    requestOptions.body = JSON.stringify(data)
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, requestOptions)
  const responseBody = await parseResponse(response)

  if (!response.ok) {
    throw new Error(getErrorMessage(responseBody))
  }

  return responseBody
}
