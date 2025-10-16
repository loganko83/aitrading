'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import QRCode from 'qrcode';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

function VerifyOTPContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const userId = searchParams.get('userId');

  const [otpCode, setOtpCode] = useState('');
  const [qrCodeUrl, setQrCodeUrl] = useState('');
  const [otpSecret, setOtpSecret] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [setupComplete, setSetupComplete] = useState(false);

  useEffect(() => {
    // Fetch OTP setup info from signup response or API
    const fetchOTPInfo = async () => {
      try {
        // In real implementation, fetch from API
        // For now, get from sessionStorage (set during signup)
        const otpData = sessionStorage.getItem('otpSetup');
        if (otpData) {
          const { secret, qrUrl } = JSON.parse(otpData);
          setOtpSecret(secret);

          // Generate QR code
          const qr = await QRCode.toDataURL(qrUrl);
          setQrCodeUrl(qr);
        }
      } catch (err) {
        console.error('Error fetching OTP info:', err);
      }
    };

    fetchOTPInfo();
  }, []);

  const handleVerify = async () => {
    if (otpCode.length !== 6) {
      setError('OTP code must be 6 digits');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/auth/verify-otp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          userId,
          otpCode,
        }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.error || 'Verification failed');
      }

      setSetupComplete(true);

      // Clear OTP setup data
      sessionStorage.removeItem('otpSetup');

      // Redirect to login after 2 seconds
      setTimeout(() => {
        router.push('/login?otp=verified');
      }, 2000);
    } catch (err: any) {
      setError(err.message || 'Verification failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    // Allow skip for now, but mark OTP as not enabled
    sessionStorage.removeItem('otpSetup');
    router.push('/login');
  };

  if (setupComplete) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-secondary p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6 text-center">
            <div className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold mb-2">2FA Setup Complete!</h2>
            <p className="text-muted-foreground">
              Your account is now protected with two-factor authentication.
            </p>
            <p className="text-sm text-muted-foreground mt-2">
              Redirecting to login...
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-secondary p-4">
      <Card className="w-full max-w-lg">
        <CardHeader className="space-y-1">
          <div className="flex items-center justify-center mb-4">
            <div className="w-12 h-12 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-2xl">🔐</span>
            </div>
          </div>
          <CardTitle className="text-2xl text-center">Setup 2FA</CardTitle>
          <CardDescription className="text-center">
            Secure your account with Google Authenticator
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-4">
            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-semibold mb-2">Step 1: Install Google Authenticator</h3>
              <p className="text-sm text-muted-foreground">
                Download Google Authenticator app on your smartphone from the App Store or Google Play.
              </p>
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-semibold mb-3">Step 2: Scan QR Code</h3>
              {qrCodeUrl ? (
                <div className="flex flex-col items-center space-y-3">
                  <img src={qrCodeUrl} alt="QR Code" className="w-48 h-48 border-4 border-white rounded-lg" />
                  <div className="text-center">
                    <p className="text-xs text-muted-foreground mb-1">Or enter this code manually:</p>
                    <code className="text-sm bg-background px-3 py-1 rounded">{otpSecret}</code>
                  </div>
                </div>
              ) : (
                <div className="flex justify-center">
                  <div className="w-48 h-48 bg-background animate-pulse rounded-lg"></div>
                </div>
              )}
            </div>

            <div className="p-4 bg-muted rounded-lg">
              <h3 className="font-semibold mb-3">Step 3: Enter Verification Code</h3>
              <div className="space-y-3">
                <Label htmlFor="otpCode">6-Digit Code from App</Label>
                <Input
                  id="otpCode"
                  type="text"
                  placeholder="000000"
                  maxLength={6}
                  value={otpCode}
                  onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
                  disabled={isLoading}
                  className="text-center text-2xl tracking-widest"
                />
              </div>
            </div>
          </div>

          {error && (
            <div className="p-3 text-sm text-destructive bg-destructive/10 rounded-md">
              {error}
            </div>
          )}

          <div className="space-y-3">
            <Button
              onClick={handleVerify}
              className="w-full"
              disabled={isLoading || otpCode.length !== 6}
            >
              {isLoading ? 'Verifying...' : 'Verify & Enable 2FA'}
            </Button>

            <Button
              onClick={handleSkip}
              variant="outline"
              className="w-full"
              disabled={isLoading}
            >
              Skip for Now
            </Button>
          </div>

          <p className="text-xs text-center text-muted-foreground">
            You can enable 2FA later from your account settings
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

export default function VerifyOTPPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <VerifyOTPContent />
    </Suspense>
  );
}
