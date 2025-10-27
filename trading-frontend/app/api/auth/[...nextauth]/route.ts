import NextAuth, { User } from 'next-auth';
import type { NextAuthConfig } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { login as backendLogin } from '@/lib/api/auth';

// Extend the built-in session types
declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      email: string;
      name: string;
      accessToken: string;
      refreshToken: string;
      is_2fa_enabled: boolean;
    };
  }

  interface User {
    id: string;
    email: string;
    name: string;
    accessToken: string;
    refreshToken: string;
    is_2fa_enabled: boolean;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string;
    email: string;
    name: string;
    accessToken: string;
    refreshToken: string;
    is_2fa_enabled: boolean;
  }
}

export const authOptions: NextAuthConfig = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
        totp_code: { label: 'OTP Code (if enabled)', type: 'text', optional: true },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Email and password required');
        }

        try {
          // Call backend login API
          const response = await backendLogin({
            email: credentials.email as string,
            password: credentials.password as string,
            // Only include totp_code if it's a non-empty string
            totp_code: credentials.totp_code && credentials.totp_code !== 'undefined' ? (credentials.totp_code as string) : undefined,
          });

          // Check if 2FA is required
          if (response.requires_2fa) {
            throw new Error('OTP_REQUIRED');
          }

          // Login successful
          if (!response.access_token || !response.refresh_token) {
            throw new Error('Invalid credentials');
          }

          return {
            id: response.user_id,
            email: response.email,
            name: response.email.split('@')[0], // Use email username as name
            accessToken: response.access_token,
            refreshToken: response.refresh_token,
            is_2fa_enabled: response.requires_2fa,
          };
        } catch (error) {
          // Re-throw specific errors
          if (error instanceof Error) {
            throw error;
          }
          throw new Error('Authentication failed');
        }
      },
    }),
  ],
  pages: {
    signIn: '/trading/login',
    signOut: '/trading/login',
    error: '/trading/login',
  },
  callbacks: {
    async jwt({ token, user }) {
      // On initial sign in, add user data to token
      if (user) {
        token.id = user.id;
        token.email = user.email;
        token.name = user.name;
        token.accessToken = user.accessToken;
        token.refreshToken = user.refreshToken;
        token.is_2fa_enabled = user.is_2fa_enabled;
      }
      return token;
    },
    async session({ session, token }) {
      // Add token data to session
      if (token && session.user) {
        session.user.id = token.id;
        session.user.email = token.email;
        session.user.name = token.name;
        session.user.accessToken = token.accessToken;
        session.user.refreshToken = token.refreshToken;
        session.user.is_2fa_enabled = token.is_2fa_enabled;
      }
      return session;
    },
  },
  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },
  secret: process.env.NEXTAUTH_SECRET,
};

// Create NextAuth handlers
const { handlers } = NextAuth(authOptions);

export const { GET, POST } = handlers;
