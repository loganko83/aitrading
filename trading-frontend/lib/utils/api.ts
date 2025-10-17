/**
 * API Utility Functions
 * Centralized API calling with error handling and type safety
 */

export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public data?: any
  ) {
    super(message)
    this.name = 'APIError'
  }
}

interface FetchOptions extends RequestInit {
  timeout?: number
}

/**
 * Enhanced fetch with timeout and error handling
 */
export async function fetchWithTimeout(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { timeout = 30000, ...fetchOptions } = options

  const controller = new AbortController()
  const timeoutId = setTimeout(() => controller.abort(), timeout)

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: controller.signal,
    })

    clearTimeout(timeoutId)

    if (!response.ok) {
      const errorData = await response.json().catch(() => null)
      throw new APIError(
        errorData?.error || errorData?.message || `HTTP ${response.status}`,
        response.status,
        errorData
      )
    }

    return response
  } catch (error) {
    clearTimeout(timeoutId)

    if (error instanceof APIError) {
      throw error
    }

    if (error instanceof Error) {
      if (error.name === 'AbortError') {
        throw new APIError('Request timeout', 408)
      }
      throw new APIError(error.message)
    }

    throw new APIError('Unknown error occurred')
  }
}

/**
 * Type-safe API GET request
 */
export async function apiGet<T>(
  url: string,
  options?: FetchOptions
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    ...options,
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  return response.json()
}

/**
 * Type-safe API POST request
 */
export async function apiPost<T>(
  url: string,
  data?: any,
  options?: FetchOptions
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    ...options,
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    body: data ? JSON.stringify(data) : undefined,
  })

  return response.json()
}

/**
 * Type-safe API PUT request
 */
export async function apiPut<T>(
  url: string,
  data?: any,
  options?: FetchOptions
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    ...options,
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    body: data ? JSON.stringify(data) : undefined,
  })

  return response.json()
}

/**
 * Type-safe API DELETE request
 */
export async function apiDelete<T>(
  url: string,
  options?: FetchOptions
): Promise<T> {
  const response = await fetchWithTimeout(url, {
    ...options,
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  // DELETE might return 204 No Content
  if (response.status === 204) {
    return {} as T
  }

  return response.json()
}

/**
 * Retry logic for failed requests
 */
export async function retryRequest<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: Error

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn()
    } catch (error) {
      lastError = error as Error

      // Don't retry on client errors (4xx)
      if (error instanceof APIError && error.status && error.status < 500) {
        throw error
      }

      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
      }
    }
  }

  throw lastError!
}
