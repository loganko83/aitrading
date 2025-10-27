'use client';

import { useState } from 'react';
import { signIn } from 'next-auth/react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'z';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  totp_code: z.string().optional(),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const router = useRouter();
  const [error, setError] = useState<string>('');
  const [otpRequired, setOtpRequired] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [debugInfo, setDebugInfo] = useState<string>('');

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
  });

  const onSubmit = async (data: LoginFormData) => {
    setIsLoading(true);
    setError('');
    setDebugInfo('');

    try {
      console.log('[LOGIN] Calling signIn with:', { email: data.email, has_totp: !!data.totp_code });
      
      const result = await signIn('credentials', {
        email: data.email,
        password: data.password,
        totp_code: data.totp_code,
        redirect: false,
      });

      console.log('[LOGIN] signIn result:', result);
      setDebugInfo(JSON.stringify(result, null, 2));

      if (result?.error) {
        console.log('[LOGIN] Error:', result.error);
        if (result.error === 'OTP_REQUIRED') {
          setOtpRequired(true);
          setError('Please enter your Google Authenticator code');
        } else {
          setError(result.error);
        }
      } else if (result?.ok) {
        console.log('[LOGIN] Success! Redirecting to dashboard...');
        router.push('/dashboard');
        router.refresh();
      } else {
        console.log('[LOGIN] Unexpected result - no error but also not ok');
        setError('Login failed with unexpected response');
      }
    } catch (err) {
      console.error('[LOGIN] Exception:', err);
      setError('An unexpected error occurred: ' + (err instanceof Error ? err.message : String(err)));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className=min-h-screen flex items-center justify-center bg-gradient-to-b from-background to-secondary p-4>
      <Card className=w-full max-w-md>
        <CardHeader className=space-y-1>
          <div className=flex items-center justify-center mb-4>
            <div className=w-12 h-12 bg-primary rounded-lg flex items-center justify-center>
              <span className=text-2xl font-bold text-primary-foreground>T</span>
            </div>
          </div>
          <CardTitle className=text-2xl text-center>Welcome Back</CardTitle>
          <CardDescription className=text-center>
            Sign in to your TradingBot AI account
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className=space-y-4>
            <div className=space-y-2>
              <Label htmlFor=email>Email</Label>
              <Input
                id=email
                type=email
                placeholder=demo@example.com
                {...register('email')}
                disabled={isLoading}
              />
              {errors.email && (
                <p className=text-sm text-destructive>{errors.email.message}</p>
              )}
            </div>

            <div className=space-y-2>
              <Label htmlFor=password>Password</Label>
              <Input
                id=password
                type=password
                placeholder=••••••••
                {...register('password')}
                disabled={isLoading}
              />
              {errors.password && (
                <p className=text-sm text-destructive>{errors.password.message}</p>
              )}
            </div>

            {otpRequired && (
              <div className=space-y-2>
                <Label htmlFor=totp_code>Google Authenticator Code</Label>
                <Input
                  id=totp_code
                  type=text
                  placeholder=123456
                  maxLength={6}
                  {...register('totp_code')}
                  disabled={isLoading}
                />
              </div>
            )}

            {error && (
              <div className=p-3 text-sm text-destructive bg-destructive/10 rounded-md>
                {error}
              </div>
            )}

            {debugInfo && (
              <div className=p-3 text-xs bg-muted rounded-md>
                <pre>{debugInfo}</pre>
              </div>
            )}

            <Button
              type=submit
              className=w-full
              disabled={isLoading}
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
            </Button>

            <div className=flex items-center justify-between text-sm>
              <Link
                href=/forgot-password
                className=text-primary hover:underline
              >
                Forgot password?
              </Link>
              <Link
                href=/signup
                className=text-primary hover:underline
              >
                Create account
              </Link>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
