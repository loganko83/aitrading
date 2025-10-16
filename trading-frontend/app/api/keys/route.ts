import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { encrypt, decrypt, validateBinanceApiKey, validateBinanceApiSecret } from '@/lib/crypto';

const ENCRYPTION_KEY = process.env.ENCRYPTION_KEY || '';

if (!ENCRYPTION_KEY || ENCRYPTION_KEY.length < 32) {
  console.warn('Warning: ENCRYPTION_KEY is not set or too short. API key encryption may be insecure.');
}

// Mock storage (replace with database in production)
const apiKeysStore = new Map<string, { encrypted_api_key: string; encrypted_api_secret: string; created_at: string; last_verified: string | null; is_active: boolean }>();

/**
 * GET /api/keys - Retrieve user's API keys (decrypted for display)
 */
export async function GET(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = session.user.id;

    // TODO: Replace with actual database query
    // const apiKeys = await prisma.apiKeys.findUnique({ where: { user_id: userId } })

    const storedKeys = apiKeysStore.get(userId);

    if (!storedKeys) {
      return NextResponse.json({
        hasKeys: false,
        api_key: null,
        api_secret: null,
        created_at: null,
        last_verified: null,
        is_active: false,
      });
    }

    // Decrypt keys for display (masked)
    try {
      const apiKey = decrypt(storedKeys.encrypted_api_key, ENCRYPTION_KEY);
      const apiSecret = decrypt(storedKeys.encrypted_api_secret, ENCRYPTION_KEY);

      return NextResponse.json({
        hasKeys: true,
        api_key: apiKey,
        api_secret: apiSecret,
        created_at: storedKeys.created_at,
        last_verified: storedKeys.last_verified,
        is_active: storedKeys.is_active,
      });
    } catch (error) {
      return NextResponse.json(
        { error: 'Failed to decrypt API keys' },
        { status: 500 }
      );
    }
  } catch (error: any) {
    console.error('GET /api/keys error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/keys - Save or update user's API keys
 */
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = session.user.id;
    const { api_key, api_secret } = await request.json();

    // Validate input
    if (!api_key || !api_secret) {
      return NextResponse.json(
        { error: 'API key and secret are required' },
        { status: 400 }
      );
    }

    // Validate Binance API key format
    if (!validateBinanceApiKey(api_key)) {
      return NextResponse.json(
        { error: 'Invalid Binance API key format. Must be 64 alphanumeric characters.' },
        { status: 400 }
      );
    }

    if (!validateBinanceApiSecret(api_secret)) {
      return NextResponse.json(
        { error: 'Invalid Binance API secret format. Must be 64 alphanumeric characters.' },
        { status: 400 }
      );
    }

    // Encrypt keys
    let encryptedApiKey: string;
    let encryptedApiSecret: string;

    try {
      encryptedApiKey = encrypt(api_key, ENCRYPTION_KEY);
      encryptedApiSecret = encrypt(api_secret, ENCRYPTION_KEY);
    } catch (error) {
      return NextResponse.json(
        { error: 'Failed to encrypt API keys' },
        { status: 500 }
      );
    }

    // TODO: Replace with actual database upsert
    // await prisma.apiKeys.upsert({
    //   where: { user_id: userId },
    //   update: {
    //     encrypted_api_key: encryptedApiKey,
    //     encrypted_api_secret: encryptedApiSecret,
    //     updated_at: new Date(),
    //   },
    //   create: {
    //     user_id: userId,
    //     encrypted_api_key: encryptedApiKey,
    //     encrypted_api_secret: encryptedApiSecret,
    //   },
    // })

    // Mock storage
    apiKeysStore.set(userId, {
      encrypted_api_key: encryptedApiKey,
      encrypted_api_secret: encryptedApiSecret,
      created_at: new Date().toISOString(),
      last_verified: null,
      is_active: true,
    });

    return NextResponse.json({
      success: true,
      message: 'API keys saved successfully',
    });
  } catch (error: any) {
    console.error('POST /api/keys error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/keys - Delete user's API keys
 */
export async function DELETE(request: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = session.user.id;

    // TODO: Replace with actual database delete
    // await prisma.apiKeys.delete({ where: { user_id: userId } })

    // Mock storage
    apiKeysStore.delete(userId);

    return NextResponse.json({
      success: true,
      message: 'API keys deleted successfully',
    });
  } catch (error: any) {
    console.error('DELETE /api/keys error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
