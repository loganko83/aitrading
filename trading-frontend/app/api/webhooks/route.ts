import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from '@/lib/auth';
import { z } from 'zod';
import { generateWebhookId, generateWebhookSecret, generateWebhookUrl } from '@/lib/webhook';
import type { Webhook } from '@/types';

// Validation schema for webhook creation
const createWebhookSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).optional(),
  is_active: z.boolean().default(true),
});

// Mock webhooks storage (will be replaced with database)
const mockWebhooks: Map<string, Webhook[]> = new Map();

// GET - List user webhooks
export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession();

    if (!session?.user?.email) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userWebhooks = mockWebhooks.get(session.user.email) || [];

    return NextResponse.json({
      success: true,
      data: userWebhooks,
    });
  } catch (error) {
    console.error('Webhooks GET error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve webhooks' },
      { status: 500 }
    );
  }
}

// POST - Create new webhook
export async function POST(req: NextRequest) {
  try {
    const session = await getServerSession();

    if (!session?.user?.email) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const body = await req.json();

    // Validate request body
    const validationResult = createWebhookSchema.safeParse(body);

    if (!validationResult.success) {
      return NextResponse.json(
        {
          success: false,
          error: 'Validation failed',
          details: validationResult.error.issues,
        },
        { status: 400 }
      );
    }

    const { name, description, is_active } = validationResult.data;

    // Generate webhook ID and secret
    const webhookId = generateWebhookId();
    const secretToken = generateWebhookSecret();
    const webhookUrl = generateWebhookUrl(session.user.email, webhookId);

    // Create webhook object
    const newWebhook: Webhook = {
      id: webhookId,
      user_id: session.user.email,
      webhook_url: webhookUrl,
      secret_token: secretToken,
      is_active,
      total_triggers: 0,
      created_at: new Date().toISOString(),
    };

    // Add name and description as metadata (not in type, but useful for UI)
    const webhookWithMetadata = {
      ...newWebhook,
      name,
      description,
    };

    // Store webhook
    const userWebhooks = mockWebhooks.get(session.user.email) || [];
    userWebhooks.push(webhookWithMetadata as any);
    mockWebhooks.set(session.user.email, userWebhooks);

    return NextResponse.json({
      success: true,
      data: webhookWithMetadata,
      message: 'Webhook created successfully',
    });
  } catch (error) {
    console.error('Webhooks POST error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to create webhook' },
      { status: 500 }
    );
  }
}

// DELETE - Delete webhook
export async function DELETE(req: NextRequest) {
  try {
    const session = await getServerSession();

    if (!session?.user?.email) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(req.url);
    const webhookId = searchParams.get('id');

    if (!webhookId) {
      return NextResponse.json(
        { success: false, error: 'Webhook ID is required' },
        { status: 400 }
      );
    }

    const userWebhooks = mockWebhooks.get(session.user.email) || [];
    const filteredWebhooks = userWebhooks.filter((w) => w.id !== webhookId);

    if (filteredWebhooks.length === userWebhooks.length) {
      return NextResponse.json(
        { success: false, error: 'Webhook not found' },
        { status: 404 }
      );
    }

    mockWebhooks.set(session.user.email, filteredWebhooks);

    return NextResponse.json({
      success: true,
      message: 'Webhook deleted successfully',
    });
  } catch (error) {
    console.error('Webhooks DELETE error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to delete webhook' },
      { status: 500 }
    );
  }
}
