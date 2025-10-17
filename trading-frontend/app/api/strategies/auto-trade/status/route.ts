import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'

export async function GET(request: Request) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/strategies/auto-trade/status`,
      {
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error fetching auto-trade status:', error)
    return NextResponse.json(
      { error: 'Failed to fetch auto-trade status' },
      { status: 500 }
    )
  }
}
