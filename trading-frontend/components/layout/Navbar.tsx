'use client';

import { useSession } from 'next-auth/react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Bell } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Navbar() {
  const { data: session } = useSession();

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  const calculateLevel = (xp: number) => {
    return Math.floor(xp / 1000) + 1;
  };

  return (
    <div className="flex h-16 items-center justify-between border-b bg-card px-6">
      <div>
        <h1 className="text-2xl font-bold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          Welcome back, {session?.user?.name}
        </p>
      </div>

      <div className="flex items-center space-x-4">
        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute top-1 right-1 h-2 w-2 rounded-full bg-red-500"></span>
        </Button>

        {/* User Profile */}
        <div className="flex items-center space-x-3">
          <div className="text-right">
            <p className="text-sm font-medium">{session?.user?.name}</p>
            <div className="flex items-center space-x-2">
              <Badge variant="secondary" className="text-xs">
                Level {session?.user?.level || calculateLevel(session?.user?.xp_points || 0)}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {session?.user?.xp_points || 0} XP
              </span>
            </div>
          </div>
          <Avatar>
            <AvatarFallback className="bg-primary text-primary-foreground">
              {session?.user?.name ? getInitials(session.user.name) : 'U'}
            </AvatarFallback>
          </Avatar>
        </div>
      </div>
    </div>
  );
}
