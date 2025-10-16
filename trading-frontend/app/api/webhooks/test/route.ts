import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { createWebhookSignature } from '@/lib/webhook';

// POST - Test webhook by sending a sample signal
export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.email) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await req.json();
    const { webhook_url, secret_token, signal } = body;

    if (!webhook_url || !secret_token) {
      return NextResponse.json(
        { success: false, error: 'Webhook URL and secret token are required' },
        { status: 400 }
      );
    }

    // Default test signal
    const testSignal = signal || {
      action: 'BUY',
      symbol: 'BTC/USDT',
      price: 43500,
      timestamp: Date.now(),
    };

    const payload = JSON.stringify(testSignal);

    // Create signature
    const signature = createWebhookSignature(payload, secret_token);

    // Send webhook request
    const response = await fetch(webhook_url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Webhook-Signature': signature,
      },
      body: payload,
    });

    const responseData = await response.json();

    return NextResponse.json({
      success: response.ok,
      status: response.status,
      data: responseData,
      test_signal: testSignal,
    });
  } catch (error) {
    console.error('Webhook test error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to test webhook' },
      { status: 500 }
    );
  }
}
