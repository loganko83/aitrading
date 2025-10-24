/**
 * Strategy Management API Client
 *
 * Pine Script strategy library and AI-powered strategy generation
 */

import { apiGet, apiPost } from './client';

// ==================== Types ====================

export interface StrategyTemplate {
  id: string;
  name: string;
  description: string;
  author: string;
  category: string;
  difficulty: string;
  popularity_score: number;
  indicators: string[];
  default_parameters: Record<string, any>;
  backtest_results?: {
    win_rate?: number;
    profit_factor?: number;
    sharpe_ratio?: number;
    max_drawdown?: number;
  };
}

export interface CustomizeStrategyRequest {
  strategy_id: string;
  account_id: string;
  webhook_secret: string;
  custom_parameters?: Record<string, any>;
  symbol?: string;
}

export interface CustomizeStrategyResponse {
  strategy_id: string;
  strategy_name: string;
  pine_script_code: string;
  parameters: Record<string, any>;
  instructions: string[];
}

export interface AnalyzePineScriptRequest {
  code: string;
  include_ai_analysis?: boolean;
}

export interface StrategyAnalysisResponse {
  strategy_info: {
    name: string;
    version: string;
    description: string;
    indicators: string[];
    parameters: Record<string, any>;
    entry_conditions: string[];
    exit_conditions: string[];
    risk_management: Record<string, any>;
    has_webhook: boolean;
  };
  ai_analysis?: {
    openai_analysis?: any;
    anthropic_analysis?: any;
    consensus?: {
      average_quality_score: number;
      key_insights: string[];
    };
  };
  recommendations: string[];
  quality_score?: number;
}

export interface OptimizeParametersRequest {
  strategy_id: string;
  market_conditions: {
    volatility: 'Low' | 'Medium' | 'High';
    trend: 'Bullish' | 'Bearish' | 'Neutral';
    volume?: string;
  };
}

export interface OptimizeParametersResponse {
  strategy_id: string;
  original_parameters: Record<string, any>;
  optimized_parameters: Record<string, any>;
  market_conditions: Record<string, any>;
  recommendation: string;
}

export interface GenerateStrategyRequest {
  description: string;
  account_id: string;
  webhook_secret: string;
  risk_level?: 'Low' | 'Medium' | 'High';
  preferred_indicators?: string[];
}

export interface GenerateStrategyResponse {
  success: boolean;
  pine_script_code: string;
  description: string;
  risk_level: string;
  warnings: string[];
  instructions: string[];
}

// ==================== API Functions ====================

/**
 * Get list of strategy templates
 */
export async function getStrategyList(
  category?: string,
  difficulty?: string,
  min_popularity?: number
): Promise<StrategyTemplate[]> {
  const params = new URLSearchParams();
  if (category) params.append('category', category);
  if (difficulty) params.append('difficulty', difficulty);
  if (min_popularity !== undefined) params.append('min_popularity', min_popularity.toString());

  const queryString = params.toString();
  const endpoint = queryString ? `/pine-script/strategies?${queryString}` : '/pine-script/strategies';

  return apiGet<StrategyTemplate[]>(endpoint);
}

/**
 * Get specific strategy template
 */
export async function getStrategy(strategyId: string): Promise<StrategyTemplate> {
  return apiGet<StrategyTemplate>(`/pine-script/strategies/${strategyId}`);
}

/**
 * Customize strategy with webhook integration
 */
export async function customizeStrategy(
  request: CustomizeStrategyRequest
): Promise<CustomizeStrategyResponse> {
  return apiPost<CustomizeStrategyResponse>('/pine-script/customize', request);
}

/**
 * Analyze Pine Script code
 */
export async function analyzePineScript(
  request: AnalyzePineScriptRequest
): Promise<StrategyAnalysisResponse> {
  return apiPost<StrategyAnalysisResponse>('/pine-script/analyze', request);
}

/**
 * Optimize strategy parameters based on market conditions
 */
export async function optimizeParameters(
  request: OptimizeParametersRequest
): Promise<OptimizeParametersResponse> {
  return apiPost<OptimizeParametersResponse>('/pine-script/optimize-parameters', request);
}

/**
 * Generate strategy using AI
 */
export async function generateStrategy(
  request: GenerateStrategyRequest
): Promise<GenerateStrategyResponse> {
  return apiPost<GenerateStrategyResponse>('/pine-script/generate', request);
}

export default {
  getStrategyList,
  getStrategy,
  customizeStrategy,
  analyzePineScript,
  optimizeParameters,
  generateStrategy,
};
