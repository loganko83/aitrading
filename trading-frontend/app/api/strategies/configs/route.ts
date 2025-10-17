import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8001'

export async function POST(request: Request) {
  try {
    const body = await request.json()

    const response = await fetch(`${BACKEND_URL}/api/v1/strategies/configs`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(error, { status: response.status })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Error creating strategy config:', error)
    return NextResponse.json(
      { error: 'Failed to create strategy config' },
      { status: 500 }
    )
  }
}
