'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Trophy,
  Medal,
  Award,
  TrendingUp,
  TrendingDown,
  Loader2,
  ChevronLeft,
  ChevronRight,
  ArrowUpDown,
} from 'lucide-react';
import type { LeaderboardEntry } from '@/types';
import { getUserInitials, getLevelTitle, formatNumber } from '@/lib/gamification';

type SortField = 'rank' | 'total_pnl' | 'xp_points' | 'win_rate' | 'total_trades';
type SortDirection = 'asc' | 'desc';

export default function LeaderboardPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [entries, setEntries] = useState<LeaderboardEntry[]>([]);
  const [currentUser, setCurrentUser] = useState<LeaderboardEntry | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [sortBy, setSortBy] = useState<SortField>('total_pnl');
  const [sortDir, setSortDir] = useState<SortDirection>('desc');

  useEffect(() => {
    loadLeaderboard();
  }, [page, sortBy, sortDir]);

  const loadLeaderboard = async () => {
    setIsLoading(true);
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        limit: '20',
        sortBy,
        sortDir,
      });

      const res = await fetch(`/api/leaderboard?${params}`);
      const result = await res.json();

      if (result.success && result.data) {
        setEntries(result.data.entries);
        setCurrentUser(result.data.currentUser);
        setTotalPages(result.data.pagination.totalPages);
      }
    } catch (error) {
      console.error('Failed to load leaderboard:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSort = (field: SortField) => {
    if (sortBy === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDir('desc');
    }
  };

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="w-6 h-6 text-yellow-500" />;
    if (rank === 2) return <Medal className="w-6 h-6 text-gray-400" />;
    if (rank === 3) return <Award className="w-6 h-6 text-amber-600" />;
    return <span className="text-sm font-semibold text-gray-600">#{rank}</span>;
  };

  const getRankBgColor = (rank: number) => {
    if (rank === 1) return 'bg-gradient-to-r from-yellow-50 to-yellow-100 border-yellow-300';
    if (rank === 2) return 'bg-gradient-to-r from-gray-50 to-gray-100 border-gray-300';
    if (rank === 3) return 'bg-gradient-to-r from-amber-50 to-amber-100 border-amber-300';
    return '';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Leaderboard</h1>
        <p className="text-gray-600 mt-2">
          Compare your performance with other traders and check your ranking
        </p>
      </div>

      {/* Current User Stats Card */}
      {currentUser && (
        <Card className="border-2 border-blue-500 bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="w-5 h-5 text-blue-600" />
              My Rank
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div>
                <div className="text-sm text-gray-600">Rank</div>
                <div className="text-2xl font-bold text-blue-600">#{currentUser.rank}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Level</div>
                <div className="text-2xl font-bold text-indigo-600">Lv.{currentUser.level}</div>
                <div className="text-xs text-gray-500">{getLevelTitle(currentUser.level)}</div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Total Profit</div>
                <div className={`text-2xl font-bold ${currentUser.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  ${currentUser.total_pnl.toLocaleString()}
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Win Rate</div>
                <div className="text-2xl font-bold text-purple-600">
                  {currentUser.win_rate.toFixed(1)}%
                </div>
              </div>
              <div>
                <div className="text-sm text-gray-600">Experience</div>
                <div className="text-2xl font-bold text-orange-600">
                  {formatNumber(currentUser.xp_points)} XP
                </div>
              </div>
            </div>
            {currentUser.badges.length > 0 && (
              <div className="mt-4">
                <div className="text-sm text-gray-600 mb-2">Earned Badges</div>
                <div className="flex flex-wrap gap-2">
                  {currentUser.badges.slice(0, 5).map((badge) => (
                    <Badge key={badge.id} variant="secondary" className="text-lg">
                      {badge.icon} {badge.name}
                    </Badge>
                  ))}
                  {currentUser.badges.length > 5 && (
                    <Badge variant="outline">+{currentUser.badges.length - 5} more</Badge>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Leaderboard Table */}
      <Card>
        <CardHeader>
          <CardTitle>전체 Rank</CardTitle>
          <CardDescription>
            Compare your performance with top traders
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="w-20">Rank</TableHead>
                  <TableHead>Trader</TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort('xp_points')}
                      className="font-semibold"
                    >
                      Level & XP
                      <ArrowUpDown className="ml-2 w-4 h-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort('total_pnl')}
                      className="font-semibold"
                    >
                      Total Profit
                      <ArrowUpDown className="ml-2 w-4 h-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort('win_rate')}
                      className="font-semibold"
                    >
                      Win Rate
                      <ArrowUpDown className="ml-2 w-4 h-4" />
                    </Button>
                  </TableHead>
                  <TableHead>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleSort('total_trades')}
                      className="font-semibold"
                    >
                      Total Trades
                      <ArrowUpDown className="ml-2 w-4 h-4" />
                    </Button>
                  </TableHead>
                  <TableHead>Badges</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entries.map((entry) => {
                  const isCurrentUser = currentUser?.user_id === entry.user_id;
                  return (
                    <TableRow
                      key={entry.user_id}
                      className={`${getRankBgColor(entry.rank)} ${
                        isCurrentUser ? 'border-2 border-blue-500' : ''
                      }`}
                    >
                      <TableCell>
                        <div className="flex items-center justify-center">
                          {getRankIcon(entry.rank)}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <Avatar className="w-10 h-10">
                            <AvatarFallback className="bg-gradient-to-br from-blue-500 to-purple-600 text-white text-sm font-bold">
                              {getUserInitials(entry.username)}
                            </AvatarFallback>
                          </Avatar>
                          <div>
                            <div className="font-semibold text-gray-900">
                              {entry.username}
                              {isCurrentUser && (
                                <Badge variant="default" className="ml-2 text-xs">
                                  You
                                </Badge>
                              )}
                            </div>
                            <div className="text-xs text-gray-500">
                              {getLevelTitle(entry.level)}
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div>
                          <div className="font-semibold text-indigo-600">
                            Lv.{entry.level}
                          </div>
                          <div className="text-xs text-gray-600">
                            {formatNumber(entry.xp_points)} XP
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          {entry.total_pnl >= 0 ? (
                            <TrendingUp className="w-4 h-4 text-green-600" />
                          ) : (
                            <TrendingDown className="w-4 h-4 text-red-600" />
                          )}
                          <div>
                            <div
                              className={`font-bold ${
                                entry.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                              }`}
                            >
                              ${entry.total_pnl.toLocaleString()}
                            </div>
                            <div className="text-xs text-gray-500">
                              {entry.total_pnl_pct >= 0 ? '+' : ''}
                              {entry.total_pnl_pct.toFixed(1)}%
                            </div>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="font-semibold text-purple-600">
                          {entry.win_rate.toFixed(1)}%
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2 mt-1">
                          <div
                            className="bg-purple-600 h-2 rounded-full"
                            style={{ width: `${entry.win_rate}%` }}
                          />
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="text-sm font-semibold text-gray-700">
                          {entry.total_trades}
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-1">
                          {entry.badges.slice(0, 3).map((badge) => (
                            <span key={badge.id} className="text-xl" title={badge.name}>
                              {badge.icon}
                            </span>
                          ))}
                          {entry.badges.length > 3 && (
                            <span className="text-xs text-gray-500">
                              +{entry.badges.length - 3}
                            </span>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>

          {/* Pagination */}
          <div className="flex items-center justify-between mt-6">
            <div className="text-sm text-gray-600">
              Page {page} / {totalPages}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
              >
                <ChevronLeft className="w-4 h-4" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setPage(Math.min(totalPages, page + 1))}
                disabled={page === totalPages}
              >
                Next
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
