import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'

export async function POST(request: Request) {
  try {
    const response = await fetch(
      `${BACKEND_URL}/api/v1/strategies/auto-trade/stop`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      }
    )

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(error, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error stopping auto-trade:', error)
    return NextResponse.json(
      { error: 'Failed to stop auto-trade' },
      { status: 500 }
    )
  }
}
