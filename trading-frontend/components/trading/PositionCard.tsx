'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { TrendingUp, TrendingDown, X } from 'lucide-react';
import type { Position } from '@/types';

interface PositionCardProps {
  position: Position;
  onClose?: (positionId: string) => void;
}

export default function PositionCard({ position, onClose }: PositionCardProps) {
  const isProfit = position.unrealized_pnl >= 0;
  const pnlPercentage = ((position.unrealized_pnl / (position.entry_price * position.quantity)) * 100).toFixed(2);

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CardTitle className="text-lg">{position.symbol}</CardTitle>
            <Badge variant={position.side === 'LONG' ? 'default' : 'destructive'}>
              {position.side}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {position.leverage}x
            </Badge>
          </div>
          {onClose && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => onClose(position.id)}
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* Entry and Current Price */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Entry Price</p>
            <p className="text-sm font-semibold">${position.entry_price.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Current Price</p>
            <p className="text-sm font-semibold">${position.current_price.toLocaleString()}</p>
          </div>
        </div>

        {/* Quantity and Position Value */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Quantity</p>
            <p className="text-sm font-semibold">{position.quantity}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Position Value</p>
            <p className="text-sm font-semibold">
              ${(position.current_price * position.quantity).toLocaleString()}
            </p>
          </div>
        </div>

        {/* Stop Loss and Take Profit */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-xs text-muted-foreground">Stop Loss</p>
            <p className="text-sm font-semibold text-red-600">
              ${position.stop_loss?.toLocaleString() || 'N/A'}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Take Profit</p>
            <p className="text-sm font-semibold text-green-600">
              ${position.take_profit?.toLocaleString() || 'N/A'}
            </p>
          </div>
        </div>

        {/* Unrealized PnL */}
        <div className="pt-2 border-t">
          <div className="flex items-center justify-between">
            <p className="text-sm text-muted-foreground">Unrealized PnL</p>
            <div className="flex items-center space-x-2">
              {isProfit ? (
                <TrendingUp className="h-4 w-4 text-green-600" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-600" />
              )}
              <div className="text-right">
                <p className={`text-lg font-bold ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                  ${Math.abs(position.unrealized_pnl).toLocaleString()}
                </p>
                <p className={`text-xs ${isProfit ? 'text-green-600' : 'text-red-600'}`}>
                  {isProfit ? '+' : ''}{pnlPercentage}%
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Opened At */}
        <div className="text-xs text-muted-foreground">
          Opened {new Date(position.opened_at).toLocaleString()}
        </div>
      </CardContent>
    </Card>
  );
}
