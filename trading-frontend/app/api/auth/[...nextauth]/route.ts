import NextAuth, { User } from 'next-auth';
import type { NextAuthConfig } from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';
import { compare } from 'bcryptjs';

// Extend the built-in session types
declare module 'next-auth' {
  interface Session {
    user: {
      id: string;
      email: string;
      name: string;
      xp_points: number;
      level: number;
      google_otp_enabled: boolean;
    };
  }

  interface User {
    id: string;
    email: string;
    name: string;
    xp_points: number;
    level: number;
    google_otp_enabled: boolean;
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string;
    xp_points: number;
    level: number;
    google_otp_enabled: boolean;
  }
}

// This would normally come from a database
// For now, we'll create a mock user lookup function
async function getUserByEmail(email: string) {
  // TODO: Replace with actual database query
  // Example: return await prisma.user.findUnique({ where: { email } })

  // Mock user for development
  if (email === 'demo@example.com') {
    return {
      id: '1',
      email: 'demo@example.com',
      name: 'Demo User',
      password: '$2a$10$X8qZ7Z7Z7Z7Z7Z7Z7Z7Z7e', // bcrypt hash of 'password'
      google_otp_enabled: false,
      google_otp_secret: null,
      xp_points: 1500,
      level: 5,
      created_at: new Date().toISOString(),
      last_login: new Date().toISOString(),
    };
  }
  return null;
}

export const authOptions: NextAuthConfig = {
  providers: [
    CredentialsProvider({
      name: 'Credentials',
      credentials: {
        email: { label: 'Email', type: 'email' },
        password: { label: 'Password', type: 'password' },
        otp: { label: 'OTP Code (if enabled)', type: 'text', optional: true },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          throw new Error('Email and password required');
        }

        const user = await getUserByEmail(credentials.email as string);

        if (!user) {
          throw new Error('Invalid credentials');
        }

        // Verify password
        const isValidPassword = await compare(credentials.password as string, user.password);
        if (!isValidPassword) {
          throw new Error('Invalid credentials');
        }

        // Check if OTP is required
        if (user.google_otp_enabled) {
          if (!credentials.otp) {
            // Return special response indicating OTP is needed
            throw new Error('OTP_REQUIRED');
          }

          // Verify OTP
          const speakeasy = require('speakeasy');
          const isValidOTP = speakeasy.totp.verify({
            secret: user.google_otp_secret,
            encoding: 'base32',
            token: credentials.otp as string,
            window: 2, // Allow 2 time steps before/after
          });

          if (!isValidOTP) {
            throw new Error('Invalid OTP code');
          }
        }

        // Update last login
        // TODO: await prisma.user.update({ where: { id: user.id }, data: { last_login: new Date() } })

        return {
          id: user.id,
          email: user.email,
          name: user.name,
          xp_points: user.xp_points,
          level: user.level,
          google_otp_enabled: user.google_otp_enabled,
        };
      },
    }),
  ],
  pages: {
    signIn: '/login',
    signOut: '/login',
    error: '/login',
  },
  callbacks: {
    async jwt({ token, user, trigger }) {
      // On initial sign in, add user data to token
      if (user) {
        token.id = user.id;
        token.email = user.email;
        token.name = user.name;
        token.xp_points = user.xp_points;
        token.level = user.level;
        token.google_otp_enabled = user.google_otp_enabled;
      }
      return token;
    },
    async session({ session, token }) {
      // Add token data to session
      if (token && session.user) {
        session.user.id = token.id;
        session.user.email = token.email as string;
        session.user.name = token.name as string;
        session.user.xp_points = token.xp_points;
        session.user.level = token.level;
        session.user.google_otp_enabled = token.google_otp_enabled;
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
