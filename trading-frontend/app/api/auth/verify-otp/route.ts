import { NextRequest, NextResponse } from 'next/server';
import speakeasy from 'speakeasy';

interface VerifyOtpRequestBody {
  userId: string
  otpCode: string
}

export async function POST(request: NextRequest) {
  try {
    const { userId, otpCode }: VerifyOtpRequestBody = await request.json();

    if (!userId || !otpCode) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    if (otpCode.length !== 6) {
      return NextResponse.json(
        { error: 'OTP code must be 6 digits' },
        { status: 400 }
      );
    }

    // Get user's OTP secret from database
    // TODO: Replace with actual database query
    // const user = await prisma.user.findUnique({ where: { id: userId } })

    // Mock user data for development
    const mockUser = {
      id: userId,
      google_otp_secret: 'JBSWY3DPEHPK3PXP', // This would come from database
    };

    if (!mockUser.google_otp_secret) {
      return NextResponse.json(
        { error: 'OTP not set up for this user' },
        { status: 400 }
      );
    }

    // Verify OTP code
    const isValid = speakeasy.totp.verify({
      secret: mockUser.google_otp_secret,
      encoding: 'base32',
      token: otpCode,
      window: 2, // Allow 2 time steps before/after (±60 seconds)
    });

    if (!isValid) {
      return NextResponse.json(
        { error: 'Invalid OTP code' },
        { status: 401 }
      );
    }

    // Enable 2FA for user
    // TODO: Update user in database
    // await prisma.user.update({
    //   where: { id: userId },
    //   data: { google_otp_enabled: true },
    // });

    return NextResponse.json({
      success: true,
      message: '2FA enabled successfully',
    });
  } catch (error) {
    console.error('OTP verification error:', error);
    const message = error instanceof Error ? error.message : 'Verification failed'
    return NextResponse.json(
      { error: message },
      { status: 500 }
    );
  }
}
