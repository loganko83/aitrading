/**
 * Backend API Client
 *
 * Centralized HTTP client for calling FastAPI backend
 */

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public detail?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

/**
 * Generic API request function
 */
async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('http')
    ? endpoint
    : `${BACKEND_URL}/api/v1${endpoint}`;

  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const config: RequestInit = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);

    // Handle non-JSON responses
    const contentType = response.headers.get('content-type');
    if (!contentType?.includes('application/json')) {
      if (!response.ok) {
        throw new ApiError(
          `HTTP ${response.status}: ${response.statusText}`,
          response.status
        );
      }
      return await response.text() as any;
    }

    const data = await response.json();

    if (!response.ok) {
      throw new ApiError(
        data.detail || data.message || `HTTP ${response.status}`,
        response.status,
        data
      );
    }

    return data;
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }

    // Network or other errors
    throw new ApiError(
      error instanceof Error ? error.message : 'An unknown error occurred',
      0
    );
  }
}

/**
 * GET request
 */
export async function apiGet<T = any>(
  endpoint: string,
  token?: string
): Promise<T> {
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return apiRequest<T>(endpoint, {
    method: 'GET',
    headers,
  });
}

/**
 * POST request
 */
export async function apiPost<T = any>(
  endpoint: string,
  body?: any,
  token?: string
): Promise<T> {
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return apiRequest<T>(endpoint, {
    method: 'POST',
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * PUT request
 */
export async function apiPut<T = any>(
  endpoint: string,
  body?: any,
  token?: string
): Promise<T> {
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return apiRequest<T>(endpoint, {
    method: 'PUT',
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
}

/**
 * DELETE request
 */
export async function apiDelete<T = any>(
  endpoint: string,
  token?: string
): Promise<T> {
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return apiRequest<T>(endpoint, {
    method: 'DELETE',
    headers,
  });
}

/**
 * PATCH request
 */
export async function apiPatch<T = any>(
  endpoint: string,
  body?: any,
  token?: string
): Promise<T> {
  const headers: HeadersInit = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  return apiRequest<T>(endpoint, {
    method: 'PATCH',
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
}

export default {
  get: apiGet,
  post: apiPost,
  put: apiPut,
  delete: apiDelete,
  patch: apiPatch,
};
