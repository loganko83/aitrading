import 'next-auth';
import 'next-auth/jwt';

declare module 'next-auth' {
  interface User {
    id: string;
    email: string;
    name: string;
    xp_points: number;
    level: number;
    google_otp_enabled: boolean;
  }

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
}

declare module 'next-auth/jwt' {
  interface JWT {
    id: string;
    xp_points: number;
    level: number;
    google_otp_enabled: boolean;
  }
}
