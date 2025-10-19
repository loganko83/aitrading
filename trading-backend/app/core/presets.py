"""
Trading Presets - User-Friendly Configuration

Pre-configured settings for different user levels and goals.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class PresetCategory(str, Enum):
    """Preset categories"""
    BEGINNER = "beginner"  # 초보자용
    CONSERVATIVE = "conservative"  # 보수적
    BALANCED = "balanced"  # 균형잡힌
    AGGRESSIVE = "aggressive"  # 공격적
    PROFESSIONAL = "professional"  # 전문가용


@dataclass
class TradingPreset:
    """Complete trading preset configuration"""
    id: str
    name: str
    name_ko: str
    description: str
    description_ko: str
    category: PresetCategory

    # Strategy settings
    strategy_type: str
    strategy_params: Dict

    # Risk settings
    leverage: int
    position_size_pct: float
    max_open_positions: int
    max_daily_loss_pct: float
    max_drawdown_pct: float

    # Risk/reward
    atr_sl_multiplier: float
    atr_tp_multiplier: float
    min_risk_reward_ratio: float

    # Trading settings
    recommended_symbols: List[str]
    recommended_timeframes: List[str]
    recommended_capital_min: float

    # Exchange compatibility
    compatible_exchanges: List[str]
    compatible_modes: List[str]

    # Performance expectations
    expected_win_rate: str  # "50-60%"
    expected_return_monthly: str  # "5-15%"
    expected_max_drawdown: str  # "10-15%"

    # User level
    difficulty: str  # "Easy", "Medium", "Hard"
    time_commitment: str  # "Low", "Medium", "High"


# ===== Beginner Presets =====

PRESET_BEGINNER_SAFE = TradingPreset(
    id="beginner_safe",
    name="Beginner Safe",
    name_ko="초보자 안전 모드",
    description="Perfect for first-time traders. Low risk, simple strategy.",
    description_ko="처음 트레이딩하는 분들을 위한 설정. 낮은 리스크, 간단한 전략.",
    category=PresetCategory.BEGINNER,

    strategy_type="supertrend",
    strategy_params={
        "period": 10,
        "multiplier": 3.0
    },

    leverage=1,  # No leverage for beginners
    position_size_pct=0.05,  # 5% per trade
    max_open_positions=1,  # One trade at a time
    max_daily_loss_pct=0.02,  # 2% daily loss limit
    max_drawdown_pct=0.10,  # 10% max drawdown

    atr_sl_multiplier=2.0,  # Wide stop loss
    atr_tp_multiplier=4.0,  # 2:1 risk/reward
    min_risk_reward_ratio=2.0,

    recommended_symbols=["BTCUSDT", "ETHUSDT"],
    recommended_timeframes=["1h", "4h"],
    recommended_capital_min=500.0,  # $500 minimum

    compatible_exchanges=["binance", "okx"],
    compatible_modes=["spot", "futures"],

    expected_win_rate="45-55%",
    expected_return_monthly="3-8%",
    expected_max_drawdown="5-10%",

    difficulty="Easy",
    time_commitment="Low"  # Check 1-2 times per day
)


# ===== Conservative Presets =====

PRESET_CONSERVATIVE_GROWTH = TradingPreset(
    id="conservative_growth",
    name="Conservative Growth",
    name_ko="보수적 성장",
    description="Steady growth with minimal risk. For patient traders.",
    description_ko="최소한의 리스크로 꾸준한 성장. 인내심 있는 트레이더용.",
    category=PresetCategory.CONSERVATIVE,

    strategy_type="multi_indicator",
    strategy_params={
        "min_agreement": 2  # Require 2/3 strategies to agree
    },

    leverage=2,
    position_size_pct=0.08,  # 8% per trade
    max_open_positions=2,
    max_daily_loss_pct=0.03,
    max_drawdown_pct=0.15,

    atr_sl_multiplier=1.8,
    atr_tp_multiplier=3.6,
    min_risk_reward_ratio=2.0,

    recommended_symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT"],
    recommended_timeframes=["1h", "4h"],
    recommended_capital_min=1000.0,

    compatible_exchanges=["binance", "okx"],
    compatible_modes=["futures"],

    expected_win_rate="50-60%",
    expected_return_monthly="5-12%",
    expected_max_drawdown="10-15%",

    difficulty="Easy",
    time_commitment="Medium"
)


# ===== Balanced Presets =====

PRESET_BALANCED_TRADER = TradingPreset(
    id="balanced_trader",
    name="Balanced Trader",
    name_ko="균형잡힌 트레이더",
    description="Balanced risk and reward. Most popular choice.",
    description_ko="리스크와 수익의 균형. 가장 인기있는 선택.",
    category=PresetCategory.BALANCED,

    strategy_type="supertrend",
    strategy_params={
        "period": 10,
        "multiplier": 3.0
    },

    leverage=3,
    position_size_pct=0.10,  # 10% per trade
    max_open_positions=3,
    max_daily_loss_pct=0.05,
    max_drawdown_pct=0.20,

    atr_sl_multiplier=1.5,
    atr_tp_multiplier=3.0,
    min_risk_reward_ratio=2.0,

    recommended_symbols=["BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"],
    recommended_timeframes=["15m", "1h"],
    recommended_capital_min=2000.0,

    compatible_exchanges=["binance", "okx"],
    compatible_modes=["futures"],

    expected_win_rate="55-65%",
    expected_return_monthly="10-20%",
    expected_max_drawdown="15-20%",

    difficulty="Medium",
    time_commitment="Medium"
)


# ===== Aggressive Presets =====

PRESET_AGGRESSIVE_GROWTH = TradingPreset(
    id="aggressive_growth",
    name="Aggressive Growth",
    name_ko="공격적 성장",
    description="High risk, high reward. For experienced traders.",
    description_ko="높은 리스크, 높은 수익. 경험있는 트레이더용.",
    category=PresetCategory.AGGRESSIVE,

    strategy_type="rsi_ema",
    strategy_params={
        "rsi_period": 14,
        "rsi_overbought": 70,
        "rsi_oversold": 30
    },

    leverage=5,
    position_size_pct=0.15,  # 15% per trade
    max_open_positions=5,
    max_daily_loss_pct=0.08,
    max_drawdown_pct=0.25,

    atr_sl_multiplier=1.2,
    atr_tp_multiplier=3.0,
    min_risk_reward_ratio=2.5,

    recommended_symbols=["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT"],
    recommended_timeframes=["5m", "15m"],
    recommended_capital_min=5000.0,

    compatible_exchanges=["binance", "okx"],
    compatible_modes=["futures"],

    expected_win_rate="50-60%",
    expected_return_monthly="20-40%",
    expected_max_drawdown="20-30%",

    difficulty="Hard",
    time_commitment="High"
)


# ===== Professional Presets =====

PRESET_PROFESSIONAL = TradingPreset(
    id="professional",
    name="Professional Trader",
    name_ko="전문가 모드",
    description="Full control, advanced strategies. For professionals only.",
    description_ko="완전한 제어, 고급 전략. 전문가 전용.",
    category=PresetCategory.PROFESSIONAL,

    strategy_type="multi_indicator",
    strategy_params={
        "min_agreement": 2,
        "use_volume_filter": True
    },

    leverage=10,
    position_size_pct=0.10,  # 10% per trade but with 10x leverage
    max_open_positions=10,
    max_daily_loss_pct=0.10,
    max_drawdown_pct=0.30,

    atr_sl_multiplier=1.5,
    atr_tp_multiplier=3.0,
    min_risk_reward_ratio=2.0,

    recommended_symbols=[
        "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
        "XRPUSDT", "ADAUSDT", "DOGEUSDT", "MATICUSDT"
    ],
    recommended_timeframes=["1m", "5m", "15m", "1h"],
    recommended_capital_min=10000.0,

    compatible_exchanges=["binance", "okx"],
    compatible_modes=["futures"],

    expected_win_rate="60-70%",
    expected_return_monthly="30-60%",
    expected_max_drawdown="25-35%",

    difficulty="Expert",
    time_commitment="Very High"
)


# ===== Preset Registry =====

PRESETS: Dict[str, TradingPreset] = {
    "beginner_safe": PRESET_BEGINNER_SAFE,
    "conservative_growth": PRESET_CONSERVATIVE_GROWTH,
    "balanced_trader": PRESET_BALANCED_TRADER,
    "aggressive_growth": PRESET_AGGRESSIVE_GROWTH,
    "professional": PRESET_PROFESSIONAL
}

# List of all presets (for cache initialization)
ALL_PRESETS = list(PRESETS.values())


def get_preset(preset_id: str) -> Optional[TradingPreset]:
    """Get preset by ID"""
    return PRESETS.get(preset_id)


def list_presets(
    category: Optional[PresetCategory] = None,
    min_capital: Optional[float] = None
) -> List[TradingPreset]:
    """
    List available presets with optional filtering

    Args:
        category: Filter by category
        min_capital: Filter by minimum capital requirement

    Returns:
        List of matching presets
    """
    presets = list(PRESETS.values())

    if category:
        presets = [p for p in presets if p.category == category]

    if min_capital:
        presets = [p for p in presets if p.recommended_capital_min <= min_capital]

    return presets


def get_preset_for_user(
    capital: float,
    experience_level: str = "beginner",  # beginner, intermediate, advanced
    risk_tolerance: str = "low"  # low, medium, high
) -> TradingPreset:
    """
    Recommend preset based on user profile

    Args:
        capital: Available capital
        experience_level: User experience level
        risk_tolerance: Risk tolerance

    Returns:
        Best matching preset
    """
    # Map user profile to preset
    preset_map = {
        ("beginner", "low"): "beginner_safe",
        ("beginner", "medium"): "conservative_growth",
        ("beginner", "high"): "balanced_trader",
        ("intermediate", "low"): "conservative_growth",
        ("intermediate", "medium"): "balanced_trader",
        ("intermediate", "high"): "aggressive_growth",
        ("advanced", "low"): "balanced_trader",
        ("advanced", "medium"): "aggressive_growth",
        ("advanced", "high"): "professional"
    }

    preset_id = preset_map.get((experience_level, risk_tolerance), "beginner_safe")
    preset = PRESETS[preset_id]

    # Check capital requirement
    if capital < preset.recommended_capital_min:
        # Downgrade to lower capital requirement
        for p in ["beginner_safe", "conservative_growth", "balanced_trader"]:
            if capital >= PRESETS[p].recommended_capital_min:
                return PRESETS[p]

    return preset


def apply_preset_to_backtest_request(
    preset_id: str,
    symbol: Optional[str] = None,
    exchange: str = "binance",
    mode: str = "futures"
) -> Dict:
    """
    Convert preset to backtest request parameters

    Args:
        preset_id: Preset ID
        symbol: Trading symbol (uses preset default if not provided)
        exchange: Exchange name
        mode: Trading mode

    Returns:
        Dictionary of backtest request parameters
    """
    preset = PRESETS.get(preset_id)
    if not preset:
        raise ValueError(f"Unknown preset: {preset_id}")

    # Get exchange configuration
    from app.core.exchange_config import get_exchange_config, convert_symbol_format

    exchange_config = get_exchange_config(exchange, mode)

    # Select symbol
    if not symbol:
        # Use first recommended symbol, converted to exchange format
        symbol = preset.recommended_symbols[0]
        symbol = convert_symbol_format(symbol, exchange)

    return {
        "strategy_type": preset.strategy_type,
        "symbol": symbol,
        "leverage": preset.leverage,
        "position_size_pct": preset.position_size_pct,
        "maker_fee": exchange_config.fees.maker_fee,
        "taker_fee": exchange_config.fees.taker_fee,
        "custom_params": preset.strategy_params,

        # Metadata for display
        "preset_info": {
            "name": preset.name_ko,
            "description": preset.description_ko,
            "expected_win_rate": preset.expected_win_rate,
            "expected_return_monthly": preset.expected_return_monthly,
            "difficulty": preset.difficulty,
            "time_commitment": preset.time_commitment
        }
    }
