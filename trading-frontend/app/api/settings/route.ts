import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';
import { z } from 'zod';

// Validation schema
const settingsSchema = z.object({
  risk_tolerance: z.enum(['low', 'medium', 'high']),
  selected_coins: z.array(z.enum(['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT'])).min(1),
  leverage: z.number().min(1).max(5),
  position_size_pct: z.number().min(0.05).max(0.20),
  stop_loss_atr_multiplier: z.number().min(1.0).max(3.0),
  take_profit_atr_multiplier: z.number().min(2.0).max(5.0),
  auto_close_on_reversal: z.boolean().default(true),
});

// GET endpoint - Retrieve user settings
export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession(authOptions);

    if (!session?.user?.email) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    // TODO: Replace with actual database query
    // For now, return default settings
    const defaultSettings = {
      id: 'default-id',
      user_id: session.user.email,
      risk_tolerance: 'medium' as const,
      selected_coins: ['BTC/USDT', 'ETH/USDT'],
      leverage: 5,
      position_size_pct: 0.10,
      stop_loss_atr_multiplier: 1.2,
      take_profit_atr_multiplier: 2.5,
      auto_close_on_reversal: true,
      auto_trade_enabled: false,
    };

    return NextResponse.json({
      success: true,
      data: defaultSettings,
    });
  } catch (error) {
    console.error('Settings GET error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve settings' },
      { status: 500 }
    );
  }
}

// POST endpoint - Save/Update settings
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

    // Validate request body
    const validationResult = settingsSchema.safeParse(body);

    if (!validationResult.success) {
      return NextResponse.json(
        {
          success: false,
          error: 'Validation failed',
          details: validationResult.error.errors
        },
        { status: 400 }
      );
    }

    const settings = validationResult.data;

    // TODO: Save to database
    console.log('Saving settings for user:', session.user.email, settings);

    // For now, return the saved settings with mock data
    const savedSettings = {
      id: 'generated-id',
      user_id: session.user.email,
      ...settings,
      auto_trade_enabled: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    return NextResponse.json({
      success: true,
      data: savedSettings,
      message: 'Settings saved successfully',
    });
  } catch (error) {
    console.error('Settings POST error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to save settings' },
      { status: 500 }
    );
  }
}
