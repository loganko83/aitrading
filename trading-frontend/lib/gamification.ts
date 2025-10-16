import type { Badge, LeaderboardEntry } from '@/types';

// XP Calculation Constants
export const XP_REWARDS = {
  WIN_TRADE: 50,
  PROFIT_10_PERCENT: 100,
  PROFIT_25_PERCENT: 250,
  PROFIT_50_PERCENT: 500,
  FIRST_TRADE: 100,
  TEN_WINS: 300,
  TWENTY_WINS: 600,
  FIFTY_WINS: 1500,
  WIN_STREAK_3: 150,
  WIN_STREAK_5: 300,
  WIN_STREAK_10: 750,
  TOTAL_PROFIT_1000: 500,
  TOTAL_PROFIT_5000: 1500,
  TOTAL_PROFIT_10000: 3000,
} as const;

// Level System
export const calculateLevel = (xp: number): number => {
  return Math.floor(xp / 1000) + 1;
};

export const calculateNextLevelXP = (currentXP: number): number => {
  const currentLevel = calculateLevel(currentXP);
  return currentLevel * 1000;
};

export const calculateLevelProgress = (xp: number): number => {
  const remainder = xp % 1000;
  return (remainder / 1000) * 100;
};

// Level Titles
export const getLevelTitle = (level: number): string => {
  if (level >= 50) return 'Legendary Trader';
  if (level >= 40) return 'Master Trader';
  if (level >= 30) return 'Expert Trader';
  if (level >= 20) return 'Pro Trader';
  if (level >= 10) return 'Advanced Trader';
  if (level >= 5) return 'Intermediate Trader';
  return 'Novice Trader';
};

// XP Calculation for Trade Results
export const calculateTradeXP = (params: {
  isWin: boolean;
  profitPercent: number;
  currentStreak: number;
  totalWins: number;
  totalProfitUSDT: number;
}): { xp: number; reasons: string[] } => {
  let totalXP = 0;
  const reasons: string[] = [];

  if (params.isWin) {
    // Base win reward
    totalXP += XP_REWARDS.WIN_TRADE;
    reasons.push(`승리 거래: +${XP_REWARDS.WIN_TRADE} XP`);

    // Profit percentage bonuses
    if (params.profitPercent >= 50) {
      totalXP += XP_REWARDS.PROFIT_50_PERCENT;
      reasons.push(`50% 이상 수익: +${XP_REWARDS.PROFIT_50_PERCENT} XP`);
    } else if (params.profitPercent >= 25) {
      totalXP += XP_REWARDS.PROFIT_25_PERCENT;
      reasons.push(`25% 이상 수익: +${XP_REWARDS.PROFIT_25_PERCENT} XP`);
    } else if (params.profitPercent >= 10) {
      totalXP += XP_REWARDS.PROFIT_10_PERCENT;
      reasons.push(`10% 이상 수익: +${XP_REWARDS.PROFIT_10_PERCENT} XP`);
    }

    // Win streak bonuses
    if (params.currentStreak >= 10) {
      totalXP += XP_REWARDS.WIN_STREAK_10;
      reasons.push(`10연승: +${XP_REWARDS.WIN_STREAK_10} XP`);
    } else if (params.currentStreak >= 5) {
      totalXP += XP_REWARDS.WIN_STREAK_5;
      reasons.push(`5연승: +${XP_REWARDS.WIN_STREAK_5} XP`);
    } else if (params.currentStreak >= 3) {
      totalXP += XP_REWARDS.WIN_STREAK_3;
      reasons.push(`3연승: +${XP_REWARDS.WIN_STREAK_3} XP`);
    }
  }

  return { xp: totalXP, reasons };
};

// Badge Definitions
export const AVAILABLE_BADGES: Record<string, Badge & { requirement: string }> = {
  FIRST_TRADE: {
    id: 'first-trade',
    name: '첫 거래',
    description: '첫 번째 거래 완료',
    icon: '🎯',
    requirement: 'Complete 1 trade',
    earned_at: '',
  },
  TEN_WINS: {
    id: 'ten-wins',
    name: '승리의 시작',
    description: '10회 승리 달성',
    icon: '🏆',
    requirement: 'Win 10 trades',
    earned_at: '',
  },
  FIFTY_WINS: {
    id: 'fifty-wins',
    name: '숙련자',
    description: '50회 승리 달성',
    icon: '⭐',
    requirement: 'Win 50 trades',
    earned_at: '',
  },
  PROFIT_1K: {
    id: 'profit-1k',
    name: '천 달러 수익',
    description: '누적 $1,000 수익 달성',
    icon: '💰',
    requirement: 'Earn $1,000 total profit',
    earned_at: '',
  },
  PROFIT_10K: {
    id: 'profit-10k',
    name: '만 달러 수익',
    description: '누적 $10,000 수익 달성',
    icon: '💎',
    requirement: 'Earn $10,000 total profit',
    earned_at: '',
  },
  WIN_STREAK_5: {
    id: 'streak-5',
    name: '5연승',
    description: '5연승 달성',
    icon: '🔥',
    requirement: '5 win streak',
    earned_at: '',
  },
  WIN_STREAK_10: {
    id: 'streak-10',
    name: '10연승 마스터',
    description: '10연승 달성',
    icon: '🚀',
    requirement: '10 win streak',
    earned_at: '',
  },
  HIGH_WIN_RATE: {
    id: 'high-win-rate',
    name: '정확한 예측',
    description: '승률 70% 이상 유지 (최소 20거래)',
    icon: '🎲',
    requirement: '70%+ win rate with 20+ trades',
    earned_at: '',
  },
  LEVEL_10: {
    id: 'level-10',
    name: '레벨 10 달성',
    description: '레벨 10 도달',
    icon: '📈',
    requirement: 'Reach level 10',
    earned_at: '',
  },
  LEVEL_25: {
    id: 'level-25',
    name: '레벨 25 달성',
    description: '레벨 25 도달',
    icon: '🌟',
    requirement: 'Reach level 25',
    earned_at: '',
  },
};

// Check which badges should be awarded
export const checkBadgeEligibility = (stats: {
  totalTrades: number;
  totalWins: number;
  totalProfitUSDT: number;
  winRate: number;
  maxStreak: number;
  level: number;
  currentBadges: string[];
}): Badge[] => {
  const newBadges: Badge[] = [];
  const now = new Date().toISOString();

  // First Trade
  if (stats.totalTrades >= 1 && !stats.currentBadges.includes('first-trade')) {
    newBadges.push({ ...AVAILABLE_BADGES.FIRST_TRADE, earned_at: now });
  }

  // Win Milestones
  if (stats.totalWins >= 50 && !stats.currentBadges.includes('fifty-wins')) {
    newBadges.push({ ...AVAILABLE_BADGES.FIFTY_WINS, earned_at: now });
  } else if (stats.totalWins >= 10 && !stats.currentBadges.includes('ten-wins')) {
    newBadges.push({ ...AVAILABLE_BADGES.TEN_WINS, earned_at: now });
  }

  // Profit Milestones
  if (stats.totalProfitUSDT >= 10000 && !stats.currentBadges.includes('profit-10k')) {
    newBadges.push({ ...AVAILABLE_BADGES.PROFIT_10K, earned_at: now });
  } else if (stats.totalProfitUSDT >= 1000 && !stats.currentBadges.includes('profit-1k')) {
    newBadges.push({ ...AVAILABLE_BADGES.PROFIT_1K, earned_at: now });
  }

  // Win Streaks
  if (stats.maxStreak >= 10 && !stats.currentBadges.includes('streak-10')) {
    newBadges.push({ ...AVAILABLE_BADGES.WIN_STREAK_10, earned_at: now });
  } else if (stats.maxStreak >= 5 && !stats.currentBadges.includes('streak-5')) {
    newBadges.push({ ...AVAILABLE_BADGES.WIN_STREAK_5, earned_at: now });
  }

  // Win Rate
  if (
    stats.totalTrades >= 20 &&
    stats.winRate >= 70 &&
    !stats.currentBadges.includes('high-win-rate')
  ) {
    newBadges.push({ ...AVAILABLE_BADGES.HIGH_WIN_RATE, earned_at: now });
  }

  // Level Milestones
  if (stats.level >= 25 && !stats.currentBadges.includes('level-25')) {
    newBadges.push({ ...AVAILABLE_BADGES.LEVEL_25, earned_at: now });
  } else if (stats.level >= 10 && !stats.currentBadges.includes('level-10')) {
    newBadges.push({ ...AVAILABLE_BADGES.LEVEL_10, earned_at: now });
  }

  return newBadges;
};

// Generate user initials for avatar
export const getUserInitials = (name: string): string => {
  const parts = name.trim().split(' ');
  if (parts.length >= 2) {
    return (parts[0][0] + parts[1][0]).toUpperCase();
  }
  return name.substring(0, 2).toUpperCase();
};

// Format number with K/M suffix
export const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toFixed(0);
};

// Sort leaderboard entries
export type SortField = 'rank' | 'total_pnl' | 'xp_points' | 'win_rate' | 'total_trades';
export type SortDirection = 'asc' | 'desc';

export const sortLeaderboard = (
  entries: LeaderboardEntry[],
  field: SortField,
  direction: SortDirection
): LeaderboardEntry[] => {
  const sorted = [...entries].sort((a, b) => {
    let aVal: number;
    let bVal: number;

    switch (field) {
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

    return direction === 'asc' ? aVal - bVal : bVal - aVal;
  });

  return sorted;
};
