'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp, TrendingDown, Wallet, Target } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatsWidgetProps {
  title: string;
  value: string;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: 'trending-up' | 'trending-down' | 'wallet' | 'target';
}

const iconMap = {
  'trending-up': TrendingUp,
  'trending-down': TrendingDown,
  wallet: Wallet,
  target: Target,
};

export default function StatsWidget({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
}: StatsWidgetProps) {
  const Icon = iconMap[icon];

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change && (
          <p
            className={cn(
              'text-xs mt-1',
              changeType === 'positive' && 'text-green-600',
              changeType === 'negative' && 'text-red-600',
              changeType === 'neutral' && 'text-muted-foreground'
            )}
          >
            {change}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
