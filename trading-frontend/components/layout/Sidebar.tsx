'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Settings,
  Key,
  Trophy,
  Webhook,
  BarChart3,
  LogOut,
  Zap,
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { signOut } from 'next-auth/react';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
  { name: 'Strategies', href: '/strategies', icon: Zap },
  { name: 'Trading Settings', href: '/settings', icon: Settings },
  { name: 'API Keys', href: '/api-keys', icon: Key },
  { name: 'Leaderboard', href: '/leaderboard', icon: Trophy },
  { name: 'Webhooks', href: '/webhooks', icon: Webhook },
];

export default function Sidebar() {
  const pathname = usePathname();

  const handleLogout = async () => {
    await signOut({ callbackUrl: '/' });
  };

  return (
    <div className="flex h-screen w-64 flex-col bg-card border-r">
      {/* Logo */}
      <div className="flex h-16 items-center border-b px-6">
        <Link href="/dashboard" className="flex items-center space-x-2">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <BarChart3 className="h-6 w-6 text-primary-foreground" />
          </div>
          <span className="text-xl font-bold">TradingBot AI</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navigation.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center space-x-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )}
            >
              <item.icon className="h-5 w-5" />
              <span>{item.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Logout Button */}
      <div className="border-t p-4">
        <Button
          onClick={handleLogout}
          variant="ghost"
          className="w-full justify-start"
        >
          <LogOut className="mr-3 h-5 w-5" />
          Logout
        </Button>
      </div>
    </div>
  );
}
