import { useState, useCallback } from 'react'
import { apiGet, apiPost, apiPut, apiDelete, APIError } from '@/lib/utils/api'

interface UseApiState<T> {
  data: T | null
  loading: boolean
  error: APIError | null
}

interface UseApiReturn<T> extends UseApiState<T> {
  execute: () => Promise<void>
  reset: () => void
}

/**
 * Custom hook for API calls with loading, error states, and automatic retries
 */
export function useApiGet<T>(
  url: string | null,
  options?: RequestInit
): UseApiReturn<T> {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(async () => {
    if (!url) return

    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const data = await apiGet<T>(url, options)
      setState({ data, loading: false, error: null })
    } catch (error) {
      const apiError = error instanceof APIError ? error : new APIError('Unknown error')
      setState({ data: null, loading: false, error: apiError })
    }
  }, [url, options])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, execute, reset }
}

/**
 * Hook for POST requests
 */
export function useApiPost<T, D = any>(
  url: string,
  options?: RequestInit
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(async (data: D) => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const result = await apiPost<T>(url, data, options)
      setState({ data: result, loading: false, error: null })
      return result
    } catch (error) {
      const apiError = error instanceof APIError ? error : new APIError('Unknown error')
      setState({ data: null, loading: false, error: apiError })
      throw apiError
    }
  }, [url, options])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, execute, reset }
}

/**
 * Hook for PUT requests
 */
export function useApiPut<T, D = any>(
  url: string,
  options?: RequestInit
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(async (data: D) => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const result = await apiPut<T>(url, data, options)
      setState({ data: result, loading: false, error: null })
      return result
    } catch (error) {
      const apiError = error instanceof APIError ? error : new APIError('Unknown error')
      setState({ data: null, loading: false, error: apiError })
      throw apiError
    }
  }, [url, options])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, execute, reset }
}

/**
 * Hook for DELETE requests
 */
export function useApiDelete<T>(
  url: string,
  options?: RequestInit
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(async () => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      const result = await apiDelete<T>(url, options)
      setState({ data: result, loading: false, error: null })
      return result
    } catch (error) {
      const apiError = error instanceof APIError ? error : new APIError('Unknown error')
      setState({ data: null, loading: false, error: apiError })
      throw apiError
    }
  }, [url, options])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, execute, reset }
}

/**
 * Generic mutation hook for any HTTP method
 */
export function useApiMutation<T, D = any>(
  method: 'POST' | 'PUT' | 'DELETE',
  url: string,
  options?: RequestInit
) {
  const [state, setState] = useState<UseApiState<T>>({
    data: null,
    loading: false,
    error: null,
  })

  const execute = useCallback(async (data?: D) => {
    setState(prev => ({ ...prev, loading: true, error: null }))

    try {
      let result: T
      switch (method) {
        case 'POST':
          result = await apiPost<T>(url, data, options)
          break
        case 'PUT':
          result = await apiPut<T>(url, data, options)
          break
        case 'DELETE':
          result = await apiDelete<T>(url, options)
          break
      }
      setState({ data: result, loading: false, error: null })
      return result
    } catch (error) {
      const apiError = error instanceof APIError ? error : new APIError('Unknown error')
      setState({ data: null, loading: false, error: apiError })
      throw apiError
    }
  }, [method, url, options])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, execute, reset }
}
