import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from '@/lib/auth';
import crypto from 'crypto';

/**
 * POST /api/keys/verify - Verify Binance API keys by making a test request
 */
export async function POST(request: NextRequest) {
  try {
    const session = await getServerSession();

    if (!session?.user?.id) {
      return NextResponse.json(
        { error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { api_key, api_secret } = await request.json();

    if (!api_key || !api_secret) {
      return NextResponse.json(
        { error: 'API key and secret are required' },
        { status: 400 }
      );
    }

    // Test Binance API connection
    const timestamp = Date.now();
    const queryString = `timestamp=${timestamp}`;

    // Create signature
    const signature = crypto
      .createHmac('sha256', api_secret)
      .update(queryString)
      .digest('hex');

    // Make test request to Binance API
    try {
      const response = await fetch(
        `https://fapi.binance.com/fapi/v2/account?${queryString}&signature=${signature}`,
        {
          headers: {
            'X-MBX-APIKEY': api_key,
          },
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));

        // Handle specific Binance errors
        if (response.status === 401) {
          return NextResponse.json(
            {
              success: false,
              error: 'Invalid API credentials',
              details: errorData.msg || 'Authentication failed'
            },
            { status: 400 }
          );
        }

        if (response.status === 403) {
          return NextResponse.json(
            {
              success: false,
              error: 'API key does not have required permissions',
              details: 'Please enable Futures trading permissions on your API key'
            },
            { status: 400 }
          );
        }

        return NextResponse.json(
          {
            success: false,
            error: 'API verification failed',
            details: errorData.msg || `HTTP ${response.status}`
          },
          { status: 400 }
        );
      }

      const accountData = await response.json();

      // Extract useful account information
      const accountInfo = {
        totalWalletBalance: accountData.totalWalletBalance || '0',
        availableBalance: accountData.availableBalance || '0',
        totalUnrealizedProfit: accountData.totalUnrealizedProfit || '0',
        canTrade: accountData.canTrade || false,
        canDeposit: accountData.canDeposit || false,
        canWithdraw: accountData.canWithdraw || false,
      };

      // TODO: Update database with verification timestamp
      // await prisma.apiKeys.update({
      //   where: { user_id: session.user.id },
      //   data: {
      //     last_verified: new Date(),
      //     is_active: true,
      //   },
      // })

      return NextResponse.json({
        success: true,
        message: 'API keys verified successfully',
        accountInfo,
      });
    } catch (fetchError: any) {
      console.error('Binance API request error:', fetchError);
      return NextResponse.json(
        {
          success: false,
          error: 'Failed to connect to Binance API',
          details: 'Please check your internet connection and try again'
        },
        { status: 500 }
      );
    }
  } catch (error: any) {
    console.error('POST /api/keys/verify error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}
