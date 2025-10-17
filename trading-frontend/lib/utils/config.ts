/**
 * Configuration management utilities
 * Provides smart defaults and auto-save functionality
 */

import { TradingSettings } from '@/types'

export const DEFAULT_SETTINGS: Partial<TradingSettings> = {
  leverage: 3,
  position_size_pct: 0.1,
  coins: ['BTC/USDT', 'ETH/USDT'],
  stop_loss_atr_multiplier: 1.5,
  take_profit_atr_multiplier: 3.0,
  entry_probability_threshold: 0.80,
  entry_confidence_threshold: 0.75,
  risk_tolerance: 'medium',
  auto_trade_enabled: false,
}

/**
 * Smart defaults based on risk tolerance
 */
export const getRiskBasedDefaults = (
  riskTolerance: 'low' | 'medium' | 'high'
): Partial<TradingSettings> => {
  const baseSettings: Record<string, Partial<TradingSettings>> = {
    low: {
      leverage: 2,
      position_size_pct: 0.05,
      entry_probability_threshold: 0.85,
      entry_confidence_threshold: 0.80,
      stop_loss_atr_multiplier: 1.8,
      take_profit_atr_multiplier: 3.5,
    },
    medium: {
      leverage: 3,
      position_size_pct: 0.10,
      entry_probability_threshold: 0.80,
      entry_confidence_threshold: 0.75,
      stop_loss_atr_multiplier: 1.5,
      take_profit_atr_multiplier: 3.0,
    },
    high: {
      leverage: 5,
      position_size_pct: 0.15,
      entry_probability_threshold: 0.75,
      entry_confidence_threshold: 0.70,
      stop_loss_atr_multiplier: 1.2,
      take_profit_atr_multiplier: 2.5,
    },
  }

  return baseSettings[riskTolerance] || baseSettings.medium
}

/**
 * Validate trading settings
 */
export const validateSettings = (
  settings: Partial<TradingSettings>
): { valid: boolean; errors: string[] } => {
  const errors: string[] = []

  if (settings.leverage !== undefined) {
    if (settings.leverage < 1 || settings.leverage > 5) {
      errors.push('Leverage must be between 1 and 5')
    }
  }

  if (settings.position_size_pct !== undefined) {
    if (settings.position_size_pct < 0.01 || settings.position_size_pct > 0.20) {
      errors.push('Position size must be between 1% and 20%')
    }
  }

  if (settings.entry_probability_threshold !== undefined) {
    if (
      settings.entry_probability_threshold < 0.70 ||
      settings.entry_probability_threshold > 0.90
    ) {
      errors.push('Probability threshold must be between 70% and 90%')
    }
  }

  if (settings.entry_confidence_threshold !== undefined) {
    if (
      settings.entry_confidence_threshold < 0.60 ||
      settings.entry_confidence_threshold > 0.90
    ) {
      errors.push('Confidence threshold must be between 60% and 90%')
    }
  }

  return {
    valid: errors.length === 0,
    errors,
  }
}

/**
 * Merge settings with defaults
 */
export const mergeWithDefaults = (
  userSettings: Partial<TradingSettings>
): TradingSettings => {
  const riskDefaults = userSettings.risk_tolerance
    ? getRiskBasedDefaults(userSettings.risk_tolerance)
    : {}

  return {
    ...DEFAULT_SETTINGS,
    ...riskDefaults,
    ...userSettings,
  } as TradingSettings
}

/**
 * Auto-save debounced settings
 */
export class SettingsAutoSave {
  private timeout: NodeJS.Timeout | null = null
  private delay: number

  constructor(delay: number = 1000) {
    this.delay = delay
  }

  save<T>(data: T, callback: (data: T) => Promise<void>) {
    if (this.timeout) {
      clearTimeout(this.timeout)
    }

    this.timeout = setTimeout(async () => {
      try {
        await callback(data)
        console.log('Settings auto-saved')
      } catch (error) {
        console.error('Auto-save failed:', error)
      }
    }, this.delay)
  }

  cancel() {
    if (this.timeout) {
      clearTimeout(this.timeout)
      this.timeout = null
    }
  }
}
