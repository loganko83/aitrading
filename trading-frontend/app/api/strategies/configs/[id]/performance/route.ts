import { NextResponse } from 'next/server'
import { fetchWithTimeout, APIError } from '@/lib/utils/api'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'

export async function GET(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params
    const { searchParams } = new URL(request.url)
    const range = searchParams.get('range') || '30d'

    const response = await fetchWithTimeout(
      `${BACKEND_URL}/api/v1/strategies/configs/${id}/performance?range=${range}`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
        timeout: 10000,
      }
    )

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching strategy performance data:', error)

    if (error instanceof APIError) {
      return NextResponse.json(
        { error: error.message, details: error.data },
        { status: error.status || 500 }
      )
    }

    return NextResponse.json(
      { error: 'Failed to fetch strategy performance data' },
      { status: 500 }
    )
  }
}
