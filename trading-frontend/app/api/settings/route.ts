/**
 * Settings API (Mock/Client-Side)
 * Handles: /api/settings
 * 
 * Note: Backend has no dedicated settings endpoint.
 * Settings are managed client-side via Zustand store.
 * This endpoint returns sensible defaults for initial load.
 */

import { NextRequest, NextResponse } from 'next/server';

// Default trading settings
const DEFAULT_SETTINGS = {
  risk_tolerance: 'medium',
  selected_coins: ['BTC/USDT', 'ETH/USDT'],
  leverage: 5,
  position_size_pct: 0.10,
  stop_loss_atr_multiplier: 2.0,
  take_profit_atr_multiplier: 3.0,
  auto_close_on_reversal: true,
};

export async function GET(request: NextRequest) {
  // Return default settings (client-side store will override with saved values)
  return NextResponse.json({
    success: true,
    data: DEFAULT_SETTINGS,
  });
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Validate required fields
    if (!body.risk_tolerance || !body.selected_coins || !body.leverage) {
      return NextResponse.json(
        { success: false, error: 'Missing required fields' },
        { status: 400 }
      );
    }

    // In a real implementation, this would save to backend
    // For now, return success (Zustand store persists to localStorage)
    return NextResponse.json({
      success: true,
      message: 'Settings saved successfully (client-side)',
      data: body,
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: 'Failed to save settings' },
      { status: 500 }
    );
  }
}
