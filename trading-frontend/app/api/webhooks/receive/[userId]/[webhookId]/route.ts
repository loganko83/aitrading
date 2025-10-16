import { NextRequest, NextResponse } from 'next/server';
import {
  parseTradingViewSignal,
  verifyWebhookSignature,
  checkWebhookRateLimit,
  normalizeSymbol,
  isValidSymbol,
} from '@/lib/webhook';

// Mock webhooks storage (should match the one in webhooks/route.ts)
const mockWebhooks = new Map<string, any[]>();

// Mock webhook events storage
const webhookEvents = new Map<string, any[]>();

export async function POST(
  req: NextRequest,
  { params }: { params: { userId: string; webhookId: string } }
) {
  try {
    const { userId, webhookId } = params;

    // Check rate limiting
    const rateLimit = checkWebhookRateLimit(webhookId, 60, 60000); // 60 requests per minute

    if (!rateLimit.allowed) {
      return NextResponse.json(
        {
          success: false,
          error: 'Rate limit exceeded',
          retryAfter: Math.ceil((rateLimit.resetAt - Date.now()) / 1000),
        },
        {
          status: 429,
          headers: {
            'X-RateLimit-Limit': '60',
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': rateLimit.resetAt.toString(),
          },
        }
      );
    }

    // Find webhook
    const userWebhooks = mockWebhooks.get(userId) || [];
    const webhook = userWebhooks.find((w) => w.id === webhookId);

    if (!webhook) {
      return NextResponse.json(
        { success: false, error: 'Webhook not found' },
        { status: 404 }
      );
    }

    if (!webhook.is_active) {
      return NextResponse.json(
        { success: false, error: 'Webhook is disabled' },
        { status: 403 }
      );
    }

    // Get request body
    const body = await req.text();

    // Parse signal
    const signal = parseTradingViewSignal(body);

    if (!signal) {
      return NextResponse.json(
        { success: false, error: 'Invalid signal format' },
        { status: 400 }
      );
    }

    // Validate symbol
    if (!isValidSymbol(signal.symbol)) {
      return NextResponse.json(
        {
          success: false,
          error: 'Invalid symbol format. Use format: BTC/USDT',
        },
        { status: 400 }
      );
    }

    // Normalize symbol
    signal.symbol = normalizeSymbol(signal.symbol);

    // Verify signature if provided
    const signatureHeader = req.headers.get('X-Webhook-Signature');
    if (signatureHeader) {
      const isValid = verifyWebhookSignature(body, signatureHeader, webhook.secret_token);
      if (!isValid) {
        return NextResponse.json(
          { success: false, error: 'Invalid signature' },
          { status: 401 }
        );
      }
    }

    // Store webhook event
    const event = {
      id: `evt_${Date.now()}`,
      webhook_id: webhookId,
      user_id: userId,
      type: 'signal_received' as const,
      signal,
      created_at: new Date().toISOString(),
    };

    const userEvents = webhookEvents.get(userId) || [];
    userEvents.unshift(event); // Add to beginning
    webhookEvents.set(userId, userEvents.slice(0, 100)); // Keep last 100 events

    // Update webhook trigger count
    webhook.total_triggers = (webhook.total_triggers || 0) + 1;
    webhook.last_triggered = new Date().toISOString();

    // Log signal (in production, this would trigger actual trading logic)
    console.log('📡 Webhook signal received:', {
      userId,
      webhookId,
      signal,
      timestamp: new Date().toISOString(),
    });

    // TODO: In production, process the signal:
    // 1. Validate user settings and API keys
    // 2. Check if auto-trading is enabled
    // 3. Execute trade based on signal (BUY/SELL/CLOSE)
    // 4. Record position in database
    // 5. Send notification to user

    return NextResponse.json(
      {
        success: true,
        message: 'Signal received successfully',
        data: {
          event_id: event.id,
          signal,
          processed_at: new Date().toISOString(),
        },
      },
      {
        headers: {
          'X-RateLimit-Limit': '60',
          'X-RateLimit-Remaining': rateLimit.remaining.toString(),
          'X-RateLimit-Reset': rateLimit.resetAt.toString(),
        },
      }
    );
  } catch (error) {
    console.error('Webhook receive error:', error);
    return NextResponse.json(
      { success: false, error: 'Internal server error' },
      { status: 500 }
    );
  }
}

// GET - Test endpoint to verify webhook is accessible
export async function GET(
  req: NextRequest,
  { params }: { params: { userId: string; webhookId: string } }
) {
  const { userId, webhookId } = params;

  return NextResponse.json({
    success: true,
    message: 'Webhook endpoint is active',
    webhook_id: webhookId,
    user_id: userId,
    timestamp: new Date().toISOString(),
  });
}
