/**
 * API Client Utility
 * Provides standardized fetch wrappers for API calls
 */

/**
 * Fetch wrapper for API calls
 * @param path - API path
 * @param options - Fetch options
 * @returns Fetch response
 */
export async function apiFetch(
  path: string,
  options?: RequestInit
): Promise<Response> {
  return fetch(path, options);
}

/**
 * POST request with JSON body
 * @param path - API path
 * @param data - Request body data
 * @returns Response
 */
export async function apiPost<T = any>(
  path: string,
  data: T
): Promise<Response> {
  return apiFetch(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
}

/**
 * GET request
 * @param path - API path
 * @returns Response
 */
export async function apiGet(path: string): Promise<Response> {
  return apiFetch(path, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });
}

/**
 * PUT request with JSON body
 * @param path - API path
 * @param data - Request body data
 * @returns Response
 */
export async function apiPut<T = any>(
  path: string,
  data: T
): Promise<Response> {
  return apiFetch(path, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  });
}

/**
 * DELETE request
 * @param path - API path
 * @returns Response
 */
export async function apiDelete(path: string): Promise<Response> {
  return apiFetch(path, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });
}
