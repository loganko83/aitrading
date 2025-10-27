/**
 * API Proxy Utility for Next.js App Router
 *
 * Proxies requests from frontend (/api/*) to backend (localhost:8001/api/v1/*)
 * Handles authentication tokens and cookies
 */

import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from '@/lib/auth';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001';

export interface ProxyOptions {
  method?: string;
  body?: any;
  headers?: Record<string, string>;
}

/**
 * Proxy request to backend API
 */
export async function proxyToBackend(
  request: NextRequest,
  backendPath: string,
  options: ProxyOptions = {}
): Promise<NextResponse> {
  try {
    // Get authorization from request headers
    let authHeader = request.headers.get('authorization');

    // If no auth header in request, try to get from NextAuth session
    if (\!authHeader) {
      const session = await getServerSession();
      if (session?.user?.accessToken) {
        authHeader = `Bearer ${session.user.accessToken}`;
      }
    }

    // Build backend URL
    const backendUrl = `${BACKEND_URL}/api/v1${backendPath}`;

    // Build request headers
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add authorization if present
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    // Forward cookies
    const cookies = request.headers.get('cookie');
    if (cookies) {
      headers['Cookie'] = cookies;
    }

    // Build request config
    const fetchOptions: RequestInit = {
      method: options.method || request.method,
      headers,
      credentials: 'include',
    };

    // Add body for POST/PUT/PATCH requests
    if (options.body) {
      fetchOptions.body = JSON.stringify(options.body);
    } else if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
      // Forward request body
      const body = await request.json().catch(() => null);
      if (body) {
        fetchOptions.body = JSON.stringify(body);
      }
    }

    // Make request to backend
    const response = await fetch(backendUrl, fetchOptions);

    // Get response data
    const contentType = response.headers.get('content-type');
    let data;

    if (contentType?.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    // Return response with same status code
    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Content-Type': 'application/json',
      },
    });

  } catch (error) {
    console.error('Proxy error:', error);
    return NextResponse.json(
      {
        error: 'Proxy error',
        message: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}
