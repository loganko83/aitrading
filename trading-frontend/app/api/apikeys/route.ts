import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { z } from 'zod';
import { encryptApiKey, decryptApiKey } from '@/lib/encryption';

// Mock storage (실제로는 Prisma 사용)
const mockApiKeys = new Map<string, any[]>();

const apiKeySchema = z.object({
  exchange: z.enum(['binance', 'bybit']),
  apiKey: z.string().min(1, 'API 키를 입력하세요'),
  apiSecret: z.string().min(1, 'Secret 키를 입력하세요'),
});

// GET - 사용자의 API 키 목록 조회
export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.email) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const userId = session.user.email;
    const apiKeys = mockApiKeys.get(userId) || [];

    // API 키는 마스킹하여 반환
    const maskedKeys = apiKeys.map((key) => ({
      id: key.id,
      exchange: key.exchange,
      apiKey: key.apiKey.slice(0, 8) + '...' + key.apiKey.slice(-4),
      isActive: key.isActive,
      createdAt: key.createdAt,
    }));

    return NextResponse.json({
      success: true,
      data: maskedKeys,
    });
  } catch (error) {
    console.error('API keys fetch error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to fetch API keys' },
      { status: 500 }
    );
  }
}

// POST - 새 API 키 등록
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
    const result = apiKeySchema.safeParse(body);

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: result.error.errors[0].message },
        { status: 400 }
      );
    }

    const { exchange, apiKey, apiSecret } = result.data;
    const userId = session.user.email;

    // API 키 암호화
    const encryptedApiKey = encryptApiKey(apiKey);
    const encryptedApiSecret = encryptApiKey(apiSecret);

    const newKey = {
      id: `key_${Date.now()}`,
      userId,
      exchange,
      apiKey: encryptedApiKey,
      apiSecret: encryptedApiSecret,
      isActive: true,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const userKeys = mockApiKeys.get(userId) || [];
    userKeys.push(newKey);
    mockApiKeys.set(userId, userKeys);

    return NextResponse.json({
      success: true,
      message: 'API 키가 안전하게 저장되었습니다',
      data: {
        id: newKey.id,
        exchange: newKey.exchange,
        isActive: newKey.isActive,
      },
    });
  } catch (error) {
    console.error('API key creation error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to create API key' },
      { status: 500 }
    );
  }
}

// DELETE - API 키 삭제
export async function DELETE(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.email) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(req.url);
    const keyId = searchParams.get('id');

    if (!keyId) {
      return NextResponse.json(
        { success: false, error: 'Key ID required' },
        { status: 400 }
      );
    }

    const userId = session.user.email;
    const userKeys = mockApiKeys.get(userId) || [];
    const filteredKeys = userKeys.filter((key) => key.id !== keyId);

    if (filteredKeys.length === userKeys.length) {
      return NextResponse.json(
        { success: false, error: 'API key not found' },
        { status: 404 }
      );
    }

    mockApiKeys.set(userId, filteredKeys);

    return NextResponse.json({
      success: true,
      message: 'API 키가 삭제되었습니다',
    });
  } catch (error) {
    console.error('API key deletion error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to delete API key' },
      { status: 500 }
    );
  }
}
