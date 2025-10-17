import { NextRequest, NextResponse } from 'next/server';
import { getServerSession } from '@/lib/auth';
import type { LeaderboardEntry, Badge } from '@/types';
import { calculateLevel, getLevelTitle, AVAILABLE_BADGES } from '@/lib/gamification';

// Mock leaderboard data (will be replaced with database queries)
const generateMockLeaderboard = (currentUserEmail: string): LeaderboardEntry[] => {
  const users = [
    { id: '1', username: 'TraderPro', email: 'pro@example.com', total_pnl: 15000, total_trades: 150, wins: 105 },
    { id: '2', username: 'CryptoKing', email: 'king@example.com', total_pnl: 12500, total_trades: 120, wins: 84 },
    { id: '3', username: 'AImaster', email: 'ai@example.com', total_pnl: 10000, total_trades: 95, wins: 71 },
    { id: '4', username: 'QuickTrade', email: 'quick@example.com', total_pnl: 8500, total_trades: 110, wins: 66 },
    { id: '5', username: 'SmartInvest', email: 'smart@example.com', total_pnl: 7200, total_trades: 88, wins: 62 },
    { id: '6', username: currentUserEmail, email: currentUserEmail, total_pnl: 6500, total_trades: 75, wins: 52 },
    { id: '7', username: 'FastProfit', email: 'fast@example.com', total_pnl: 5800, total_trades: 92, wins: 55 },
    { id: '8', username: 'LongTermHodl', email: 'hodl@example.com', total_pnl: 5200, total_trades: 65, wins: 45 },
    { id: '9', username: 'DayTrader', email: 'day@example.com', total_pnl: 4800, total_trades: 130, wins: 72 },
    { id: '10', username: 'SwingMaster', email: 'swing@example.com', total_pnl: 4200, total_trades: 58, wins: 38 },
    { id: '11', username: 'BTCwhale', email: 'whale@example.com', total_pnl: 3800, total_trades: 45, wins: 30 },
    { id: '12', username: 'ETHlover', email: 'eth@example.com', total_pnl: 3500, total_trades: 68, wins: 44 },
    { id: '13', username: 'AltcoinPro', email: 'alt@example.com', total_pnl: 3200, total_trades: 82, wins: 49 },
    { id: '14', username: 'TrendFollow', email: 'trend@example.com', total_pnl: 2900, total_trades: 54, wins: 35 },
    { id: '15', username: 'BreakoutHunt', email: 'breakout@example.com', total_pnl: 2600, total_trades: 71, wins: 42 },
    { id: '16', username: 'ScalpingPro', email: 'scalp@example.com', total_pnl: 2300, total_trades: 156, wins: 89 },
    { id: '17', username: 'HODLstrong', email: 'strong@example.com', total_pnl: 2000, total_trades: 38, wins: 25 },
    { id: '18', username: 'MoonSeeker', email: 'moon@example.com', total_pnl: 1800, total_trades: 95, wins: 52 },
    { id: '19', username: 'BearMarket', email: 'bear@example.com', total_pnl: 1500, total_trades: 61, wins: 36 },
    { id: '20', username: 'BullRun', email: 'bull@example.com', total_pnl: 1200, total_trades: 48, wins: 28 },
  ];

  const leaderboard: LeaderboardEntry[] = users.map((user, index) => {
    const win_rate = (user.wins / user.total_trades) * 100;
    const xp_points = user.wins * 50 + Math.floor(user.total_pnl / 10) * 100;
    const level = calculateLevel(xp_points);

    // Award badges based on achievements
    const badges: Badge[] = [];
    if (user.total_trades >= 1) {
      badges.push({ ...AVAILABLE_BADGES.FIRST_TRADE, earned_at: new Date().toISOString() });
    }
    if (user.wins >= 10) {
      badges.push({ ...AVAILABLE_BADGES.TEN_WINS, earned_at: new Date().toISOString() });
    }
    if (user.wins >= 50) {
      badges.push({ ...AVAILABLE_BADGES.FIFTY_WINS, earned_at: new Date().toISOString() });
    }
    if (user.total_pnl >= 1000) {
      badges.push({ ...AVAILABLE_BADGES.PROFIT_1K, earned_at: new Date().toISOString() });
    }
    if (user.total_pnl >= 10000) {
      badges.push({ ...AVAILABLE_BADGES.PROFIT_10K, earned_at: new Date().toISOString() });
    }
    if (level >= 10) {
      badges.push({ ...AVAILABLE_BADGES.LEVEL_10, earned_at: new Date().toISOString() });
    }
    if (level >= 25) {
      badges.push({ ...AVAILABLE_BADGES.LEVEL_25, earned_at: new Date().toISOString() });
    }

    return {
      rank: index + 1,
      user_id: user.id,
      username: user.username,
      total_pnl: user.total_pnl,
      total_pnl_pct: (user.total_pnl / 10000) * 100, // Assuming $10k starting capital
      win_rate,
      total_trades: user.total_trades,
      xp_points,
      level,
      badges,
    };
  });

  return leaderboard;
};

// GET endpoint - Retrieve leaderboard with pagination
export async function GET(req: NextRequest) {
  try {
    const session = await getServerSession();

    if (!session?.user?.email) {
      return NextResponse.json(
        { success: false, error: 'Unauthorized' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(req.url);
    const page = parseInt(searchParams.get('page') || '1');
    const limit = parseInt(searchParams.get('limit') || '20');
    const sortBy = (searchParams.get('sortBy') || 'total_pnl') as
      'rank' | 'total_pnl' | 'xp_points' | 'win_rate' | 'total_trades';
    const sortDir = (searchParams.get('sortDir') || 'desc') as 'asc' | 'desc';

    // Generate mock data
    let leaderboard = generateMockLeaderboard(session.user.email);

    // Sort leaderboard
    leaderboard.sort((a, b) => {
      let aVal: number;
      let bVal: number;

      switch (sortBy) {
        case 'rank':
          aVal = a.rank;
          bVal = b.rank;
          break;
        case 'total_pnl':
          aVal = a.total_pnl;
          bVal = b.total_pnl;
          break;
        case 'xp_points':
          aVal = a.xp_points;
          bVal = b.xp_points;
          break;
        case 'win_rate':
          aVal = a.win_rate;
          bVal = b.win_rate;
          break;
        case 'total_trades':
          aVal = a.total_trades;
          bVal = b.total_trades;
          break;
        default:
          return 0;
      }

      return sortDir === 'asc' ? aVal - bVal : bVal - aVal;
    });

    // Update ranks after sorting
    leaderboard = leaderboard.map((entry, index) => ({
      ...entry,
      rank: index + 1,
    }));

    // Paginate
    const startIndex = (page - 1) * limit;
    const endIndex = startIndex + limit;
    const paginatedData = leaderboard.slice(startIndex, endIndex);

    // Find current user's entry
    const currentUserEntry = leaderboard.find(
      (entry) => entry.username === session.user?.email
    );

    return NextResponse.json({
      success: true,
      data: {
        entries: paginatedData,
        currentUser: currentUserEntry,
        pagination: {
          page,
          limit,
          total: leaderboard.length,
          totalPages: Math.ceil(leaderboard.length / limit),
          hasNext: endIndex < leaderboard.length,
          hasPrev: page > 1,
        },
        sorting: {
          sortBy,
          sortDir,
        },
      },
    });
  } catch (error) {
    console.error('Leaderboard GET error:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to retrieve leaderboard' },
      { status: 500 }
    );
  }
}
