// Error handling utilities

/**
 * Type guard to check if error is an Error instance
 */
export function isError(error: unknown): error is Error {
  return error instanceof Error
}

/**
 * Extract error message from unknown error type
 */
export function getErrorMessage(error: unknown): string {
  if (isError(error)) {
    return error.message
  }

  if (typeof error === 'string') {
    return error
  }

  if (error && typeof error === 'object' && 'message' in error) {
    return String(error.message)
  }

  return 'An unknown error occurred'
}

/**
 * Log error with context
 */
export function logError(context: string, error: unknown): void {
  console.error(`[${context}]`, error)
}

/**
 * Handle API error and return formatted response
 */
export function handleApiError(error: unknown, defaultMessage: string = 'Operation failed'): {
  error: string
  details?: unknown
} {
  if (isError(error)) {
    return {
      error: error.message || defaultMessage,
      details: error
    }
  }

  return {
    error: defaultMessage,
    details: error
  }
}
