import NextAuth from 'next-auth';
import { authOptions } from '@/app/api/auth/[...nextauth]/route';

// Create NextAuth instance with authOptions
const { handlers, auth, signIn, signOut } = NextAuth(authOptions);

// Export auth function as getServerSession for compatibility
export const getServerSession = auth;

// Export other helpers
export { handlers, signIn, signOut };
