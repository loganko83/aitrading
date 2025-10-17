import { NextResponse } from 'next/server'
import { fetchWithTimeout, APIError } from '@/lib/utils/api'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const range = searchParams.get('range') || '30d'

    // TODO: Get user ID from session/auth
    const userId = 'user_123' // Placeholder

    const response = await fetchWithTimeout(
      `${BACKEND_URL}/api/v1/performance?user_id=${userId}&range=${range}`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 10000, // 10 second timeout for analytics data
      }
    )

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching performance data:', error)

    if (error instanceof APIError) {
      return NextResponse.json(
        { error: error.message, details: error.data },
        { status: error.status || 500 }
      )
    }

    return NextResponse.json(
      { error: 'Failed to fetch performance data' },
      { status: 500 }
    )
  }
}
