"""
Exchange-Specific Configuration

Optimized settings for Binance and OKX exchanges.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum


class Exchange(str, Enum):
    """Supported exchanges"""
    BINANCE = "binance"
    OKX = "okx"


class TradingMode(str, Enum):
    """Trading mode types"""
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"


@dataclass
class ExchangeFees:
    """Exchange fee structure"""
    maker_fee: float  # Maker fee (%)
    taker_fee: float  # Taker fee (%)

    # VIP level discounts
    vip_levels: Dict[str, Dict[str, float]] = None

    def get_fees(self, vip_level: str = "0") -> tuple:
        """Get fees for specific VIP level"""
        if self.vip_levels and vip_level in self.vip_levels:
            level_fees = self.vip_levels[vip_level]
            return level_fees['maker'], level_fees['taker']
        return self.maker_fee, self.taker_fee


@dataclass
class ExchangeLimits:
    """Exchange trading limits"""
    max_leverage: int
    min_order_size: float  # Minimum order size in USDT
    max_order_size: float  # Maximum order size in USDT
    max_positions: int  # Maximum open positions

    # Rate limits (requests per minute)
    api_rate_limit: int
    order_rate_limit: int


@dataclass
class ExchangeConfig:
    """Complete exchange configuration"""
    exchange: Exchange
    mode: TradingMode
    fees: ExchangeFees
    limits: ExchangeLimits

    # Recommended settings
    recommended_leverage: int
    recommended_position_size_pct: float

    # Optimal symbols for this exchange
    optimal_symbols: List[str]

    # Timeframes with best liquidity
    optimal_timeframes: List[str]


# ===== Binance Configuration =====

BINANCE_FUTURES_FEES = ExchangeFees(
    maker_fee=0.0002,  # 0.02%
    taker_fee=0.0004,  # 0.04%
    vip_levels={
        "0": {"maker": 0.0002, "taker": 0.0004},
        "1": {"maker": 0.00016, "taker": 0.00040},
        "2": {"maker": 0.00014, "taker": 0.00035},
        "3": {"maker": 0.00012, "taker": 0.00032},
        "4": {"maker": 0.00010, "taker": 0.00030},
        "VIP": {"maker": 0.00000, "taker": 0.00020}  # VIP 1-9
    }
)

BINANCE_FUTURES_LIMITS = ExchangeLimits(
    max_leverage=125,  # Up to 125x for BTC
    min_order_size=5.0,  # 5 USDT minimum
    max_order_size=1000000.0,  # 1M USDT
    max_positions=200,  # Binance allows many positions
    api_rate_limit=2400,  # 2400 requests per minute
    order_rate_limit=300  # 300 orders per 10 seconds = 1800/min
)

BINANCE_SPOT_FEES = ExchangeFees(
    maker_fee=0.001,  # 0.1%
    taker_fee=0.001,  # 0.1%
    vip_levels={
        "0": {"maker": 0.001, "taker": 0.001},
        "1": {"maker": 0.0009, "taker": 0.001},
        "VIP": {"maker": 0.0, "taker": 0.0008}
    }
)

BINANCE_SPOT_LIMITS = ExchangeLimits(
    max_leverage=10,  # Spot margin max 10x
    min_order_size=10.0,  # 10 USDT minimum
    max_order_size=500000.0,
    max_positions=100,
    api_rate_limit=1200,
    order_rate_limit=180
)


# ===== OKX Configuration =====

OKX_FUTURES_FEES = ExchangeFees(
    maker_fee=0.0002,  # 0.02%
    taker_fee=0.0005,  # 0.05%
    vip_levels={
        "Normal": {"maker": 0.0002, "taker": 0.0005},
        "VIP1": {"maker": 0.00015, "taker": 0.00040},
        "VIP2": {"maker": 0.00012, "taker": 0.00035},
        "VIP3": {"maker": 0.00010, "taker": 0.00032},
        "VIP4": {"maker": 0.00008, "taker": 0.00030},
        "VIP5": {"maker": 0.00005, "taker": 0.00025}
    }
)

OKX_FUTURES_LIMITS = ExchangeLimits(
    max_leverage=125,  # OKX also offers up to 125x
    min_order_size=1.0,  # 1 USDT minimum (lower than Binance)
    max_order_size=1000000.0,
    max_positions=150,
    api_rate_limit=1200,  # More conservative rate limit
    order_rate_limit=120  # 60 orders per 2 seconds = 1800/min
)

OKX_SPOT_FEES = ExchangeFees(
    maker_fee=0.001,  # 0.1%
    taker_fee=0.0015,  # 0.15%
    vip_levels={
        "Normal": {"maker": 0.001, "taker": 0.0015},
        "VIP1": {"maker": 0.0008, "taker": 0.0012}
    }
)

OKX_SPOT_LIMITS = ExchangeLimits(
    max_leverage=10,
    min_order_size=1.0,
    max_order_size=500000.0,
    max_positions=100,
    api_rate_limit=600,
    order_rate_limit=100
)


# ===== Exchange Configurations =====

EXCHANGE_CONFIGS: Dict[str, ExchangeConfig] = {
    "binance_futures": ExchangeConfig(
        exchange=Exchange.BINANCE,
        mode=TradingMode.FUTURES,
        fees=BINANCE_FUTURES_FEES,
        limits=BINANCE_FUTURES_LIMITS,
        recommended_leverage=3,  # Conservative recommendation
        recommended_position_size_pct=0.10,  # 10% per trade
        optimal_symbols=[
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
            "XRPUSDT", "ADAUSDT", "DOGEUSDT", "MATICUSDT"
        ],
        optimal_timeframes=["5m", "15m", "1h", "4h"]
    ),

    "binance_spot": ExchangeConfig(
        exchange=Exchange.BINANCE,
        mode=TradingMode.SPOT,
        fees=BINANCE_SPOT_FEES,
        limits=BINANCE_SPOT_LIMITS,
        recommended_leverage=1,  # Spot trading, no leverage
        recommended_position_size_pct=0.20,  # 20% per trade
        optimal_symbols=[
            "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT"
        ],
        optimal_timeframes=["1h", "4h", "1d"]
    ),

    "okx_futures": ExchangeConfig(
        exchange=Exchange.OKX,
        mode=TradingMode.FUTURES,
        fees=OKX_FUTURES_FEES,
        limits=OKX_FUTURES_LIMITS,
        recommended_leverage=3,
        recommended_position_size_pct=0.10,
        optimal_symbols=[
            "BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT",
            "ADA-USDT", "DOGE-USDT", "MATIC-USDT"
        ],
        optimal_timeframes=["5m", "15m", "1h", "4h"]
    ),

    "okx_spot": ExchangeConfig(
        exchange=Exchange.OKX,
        mode=TradingMode.SPOT,
        fees=OKX_SPOT_FEES,
        limits=OKX_SPOT_LIMITS,
        recommended_leverage=1,
        recommended_position_size_pct=0.20,
        optimal_symbols=[
            "BTC-USDT", "ETH-USDT", "SOL-USDT"
        ],
        optimal_timeframes=["1h", "4h", "1d"]
    )
}


def get_exchange_config(
    exchange: str = "binance",
    mode: str = "futures",
    vip_level: str = "0"
) -> ExchangeConfig:
    """
    Get exchange configuration

    Args:
        exchange: 'binance' or 'okx'
        mode: 'futures' or 'spot'
        vip_level: VIP level for fee discounts

    Returns:
        ExchangeConfig with all settings
    """
    config_key = f"{exchange.lower()}_{mode.lower()}"

    if config_key not in EXCHANGE_CONFIGS:
        # Default to Binance Futures
        config_key = "binance_futures"

    config = EXCHANGE_CONFIGS[config_key]

    # Apply VIP level fees if specified
    if vip_level != "0":
        maker, taker = config.fees.get_fees(vip_level)
        config.fees.maker_fee = maker
        config.fees.taker_fee = taker

    return config


def validate_trading_parameters(
    exchange: str,
    mode: str,
    leverage: int,
    position_size: float,
    symbol: str
) -> tuple[bool, Optional[str]]:
    """
    Validate trading parameters against exchange limits

    Args:
        exchange: Exchange name
        mode: Trading mode
        leverage: Desired leverage
        position_size: Position size in USDT
        symbol: Trading symbol

    Returns:
        (is_valid, error_message)
    """
    config = get_exchange_config(exchange, mode)

    # Check leverage
    if leverage > config.limits.max_leverage:
        return False, f"Leverage {leverage}x exceeds maximum {config.limits.max_leverage}x for {exchange} {mode}"

    # Check position size
    if position_size < config.limits.min_order_size:
        return False, f"Position size ${position_size:.2f} is below minimum ${config.limits.min_order_size}"

    if position_size > config.limits.max_order_size:
        return False, f"Position size ${position_size:.2f} exceeds maximum ${config.limits.max_order_size}"

    # Check symbol format
    if exchange == "okx" and "-" not in symbol:
        return False, f"OKX symbol format should be like 'BTC-USDT' (got '{symbol}')"

    if exchange == "binance" and "-" in symbol:
        return False, f"Binance symbol format should be like 'BTCUSDT' (got '{symbol}')"

    return True, None


def get_optimal_settings(
    exchange: str = "binance",
    mode: str = "futures",
    strategy_type: str = "supertrend"
) -> Dict:
    """
    Get optimal settings for specific exchange and strategy

    Returns recommended settings that work best for the combination.
    """
    config = get_exchange_config(exchange, mode)

    # Strategy-specific adjustments
    strategy_adjustments = {
        "supertrend": {
            "recommended_timeframes": ["5m", "15m", "1h"],
            "min_volume_filter": True,
            "optimal_leverage": 3
        },
        "rsi_ema": {
            "recommended_timeframes": ["15m", "1h", "4h"],
            "min_volume_filter": True,
            "optimal_leverage": 2
        },
        "macd_stoch": {
            "recommended_timeframes": ["1h", "4h"],
            "min_volume_filter": True,
            "optimal_leverage": 2
        },
        "ichimoku": {
            "recommended_timeframes": ["4h", "1d"],
            "min_volume_filter": False,
            "optimal_leverage": 2
        }
    }

    base_settings = {
        "exchange": exchange,
        "mode": mode,
        "maker_fee": config.fees.maker_fee,
        "taker_fee": config.fees.taker_fee,
        "recommended_leverage": config.recommended_leverage,
        "recommended_position_size_pct": config.recommended_position_size_pct,
        "optimal_symbols": config.optimal_symbols,
        "optimal_timeframes": config.optimal_timeframes,
        "max_leverage": config.limits.max_leverage,
        "min_order_size": config.limits.min_order_size
    }

    # Merge with strategy-specific settings
    if strategy_type in strategy_adjustments:
        strategy_settings = strategy_adjustments[strategy_type]
        base_settings.update({
            "recommended_timeframes": strategy_settings["recommended_timeframes"],
            "recommended_leverage": strategy_settings["optimal_leverage"]
        })

    return base_settings


# ===== Symbol Conversion =====

def convert_symbol_format(symbol: str, target_exchange: str) -> str:
    """
    Convert symbol between Binance and OKX format

    Examples:
        BTCUSDT (Binance) → BTC-USDT (OKX)
        BTC-USDT (OKX) → BTCUSDT (Binance)
    """
    if target_exchange.lower() == "okx":
        # Binance → OKX
        if "-" not in symbol:
            # Assume USDT pair
            if "USDT" in symbol:
                base = symbol.replace("USDT", "")
                return f"{base}-USDT"
            else:
                # Try to find common quote currencies
                for quote in ["USDC", "BUSD", "BTC", "ETH"]:
                    if quote in symbol:
                        base = symbol.replace(quote, "")
                        return f"{base}-{quote}"
        return symbol  # Already in OKX format

    elif target_exchange.lower() == "binance":
        # OKX → Binance
        if "-" in symbol:
            return symbol.replace("-", "")
        return symbol  # Already in Binance format

    return symbol
