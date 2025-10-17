import { NextRequest, NextResponse } from 'next/server';
import { hash } from 'bcryptjs';
import speakeasy from 'speakeasy';

interface SignupRequestBody {
  name: string
  email: string
  password: string
}

export async function POST(request: NextRequest) {
  try {
    const { name, email, password }: SignupRequestBody = await request.json();

    // Validation
    if (!name || !email || !password) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      );
    }

    if (password.length < 8) {
      return NextResponse.json(
        { error: 'Password must be at least 8 characters' },
        { status: 400 }
      );
    }

    // Check if user already exists
    // TODO: Replace with actual database query
    // const existingUser = await prisma.user.findUnique({ where: { email } })

    // Mock check for development
    if (email === 'demo@example.com') {
      return NextResponse.json(
        { error: 'User with this email already exists' },
        { status: 409 }
      );
    }

    // Hash password
    const hashedPassword = await hash(password, 10);

    // Generate Google OTP secret for 2FA
    const otpSecret = speakeasy.generateSecret({
      name: `TradingBot AI (${email})`,
      length: 32,
    });

    // Create user in database
    // TODO: Replace with actual database insert
    // const user = await prisma.user.create({
    //   data: {
    //     name,
    //     email,
    //     password: hashedPassword,
    //     google_otp_secret: otpSecret.base32,
    //     google_otp_enabled: false, // Will be enabled after verification
    //     xp_points: 0,
    //     level: 1,
    //   },
    // });

    // Mock user creation for development
    const mockUser = {
      id: Math.random().toString(36).substring(7),
      name,
      email,
      password: hashedPassword,
      google_otp_secret: otpSecret.base32,
      google_otp_enabled: false,
      xp_points: 0,
      level: 1,
      created_at: new Date().toISOString(),
    };

    // Return success with OTP setup info
    return NextResponse.json({
      success: true,
      message: 'Account created successfully',
      userId: mockUser.id,
      requireOTP: true,
      otpSecret: otpSecret.base32,
      otpQRCode: otpSecret.otpauth_url, // QR code URL for Google Authenticator
    });
  } catch (error) {
    console.error('Signup error:', error);
    const message = error instanceof Error ? error.message : 'Internal server error'
    return NextResponse.json(
      { error: message },
      { status: 500 }
    );
  }
}
