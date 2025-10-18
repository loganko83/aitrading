"""
Binance Futures Margin Calculator

Implements margin calculations according to Binance USDS-M Futures specifications:
- Initial Margin (IM) calculation
- Maintenance Margin (MM) calculation
- Margin Ratio calculation
- Liquidation price calculation
- Position sizing based on available balance
"""

from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class MarginCalculator:
    """
    Binance Futures Margin Calculator

    Formulas based on Binance official documentation:
    - Initial Margin = (Position Size × Mark Price) / Leverage
    - Maintenance Margin Rate varies by position tier
    - Liquidation occurs when Margin Ratio ≥ 100%
    """

    # Leverage tiers for BTCUSDT (example - varies by symbol)
    # Format: (max_position_value, max_leverage, maintenance_margin_rate)
    LEVERAGE_TIERS = [
        (50000, 125, 0.004),      # 0-50k USDT: 125x, 0.4% MMR
        (250000, 100, 0.005),     # 50k-250k: 100x, 0.5% MMR
        (1000000, 50, 0.01),      # 250k-1M: 50x, 1.0% MMR
        (10000000, 20, 0.025),    # 1M-10M: 20x, 2.5% MMR
        (float('inf'), 10, 0.05)  # 10M+: 10x, 5.0% MMR
    ]

    @staticmethod
    def calculate_initial_margin(
        position_size: float,
        mark_price: float,
        leverage: int
    ) -> float:
        """
        Calculate Initial Margin required for a position

        Formula: IM = (Position Size × Mark Price) / Leverage

        Args:
            position_size: Position quantity (e.g., 0.5 BTC)
            mark_price: Current mark price (e.g., $65,000)
            leverage: Leverage multiplier (1-125x)

        Returns:
            Initial margin in USDT

        Example:
            >>> MarginCalculator.calculate_initial_margin(1.0, 65000, 10)
            6500.0  # $6,500 USDT required
        """
        if leverage < 1 or leverage > 125:
            raise ValueError(f"Invalid leverage {leverage}. Must be between 1-125")

        notional_value = position_size * mark_price
        initial_margin = notional_value / leverage

        logger.debug(f"Initial Margin: {initial_margin:.2f} USDT "
                    f"(Size: {position_size}, Price: {mark_price}, Leverage: {leverage}x)")

        return initial_margin

    @staticmethod
    def get_maintenance_margin_rate(position_value: float) -> Tuple[float, int]:
        """
        Get Maintenance Margin Rate based on position value tier

        Args:
            position_value: Total position value in USDT

        Returns:
            Tuple of (maintenance_margin_rate, max_leverage)

        Example:
            >>> MarginCalculator.get_maintenance_margin_rate(100000)
            (0.005, 100)  # 0.5% MMR, 100x max leverage
        """
        for max_value, max_leverage, mmr in MarginCalculator.LEVERAGE_TIERS:
            if position_value <= max_value:
                return mmr, max_leverage

        # Fallback to highest tier
        return 0.05, 10

    @staticmethod
    def calculate_maintenance_margin(
        position_size: float,
        mark_price: float
    ) -> Tuple[float, float]:
        """
        Calculate Maintenance Margin for a position

        Args:
            position_size: Position quantity
            mark_price: Current mark price

        Returns:
            Tuple of (maintenance_margin, maintenance_margin_rate)

        Example:
            >>> MarginCalculator.calculate_maintenance_margin(1.0, 65000)
            (260.0, 0.004)  # $260 MM, 0.4% MMR
        """
        position_value = position_size * mark_price
        mmr, max_leverage = MarginCalculator.get_maintenance_margin_rate(position_value)

        maintenance_margin = position_value * mmr

        logger.debug(f"Maintenance Margin: {maintenance_margin:.2f} USDT "
                    f"(Value: {position_value:.2f}, MMR: {mmr:.2%})")

        return maintenance_margin, mmr

    @staticmethod
    def calculate_margin_ratio(
        maintenance_margin: float,
        margin_balance: float
    ) -> float:
        """
        Calculate Margin Ratio

        Formula: Margin Ratio = (Maintenance Margin / Margin Balance) × 100%

        Liquidation occurs when Margin Ratio ≥ 100%

        Args:
            maintenance_margin: Required maintenance margin
            margin_balance: Current margin balance (includes unrealized P&L)

        Returns:
            Margin ratio as percentage (0-100+)

        Example:
            >>> MarginCalculator.calculate_margin_ratio(260, 6500)
            4.0  # 4% - Safe zone
            >>> MarginCalculator.calculate_margin_ratio(260, 250)
            104.0  # 104% - Liquidation!
        """
        if margin_balance <= 0:
            return 100.0  # Immediate liquidation

        margin_ratio = (maintenance_margin / margin_balance) * 100

        if margin_ratio >= 100:
            logger.warning(f"⚠️ LIQUIDATION RISK: Margin Ratio {margin_ratio:.2f}% ≥ 100%")
        elif margin_ratio >= 80:
            logger.warning(f"⚠️ HIGH RISK: Margin Ratio {margin_ratio:.2f}%")

        return margin_ratio

    @staticmethod
    def calculate_liquidation_price(
        entry_price: float,
        position_size: float,
        side: str,
        leverage: int,
        wallet_balance: float
    ) -> float:
        """
        Calculate Liquidation Price for a position

        Simplified formula for LONG positions:
        Liquidation Price = Entry Price × (1 - Initial Margin Rate + Maintenance Margin Rate)

        For SHORT positions:
        Liquidation Price = Entry Price × (1 + Initial Margin Rate - Maintenance Margin Rate)

        Args:
            entry_price: Position entry price
            position_size: Position quantity
            side: 'LONG' or 'SHORT'
            leverage: Position leverage
            wallet_balance: Available wallet balance

        Returns:
            Liquidation price

        Example:
            >>> MarginCalculator.calculate_liquidation_price(65000, 1.0, 'LONG', 10, 7000)
            59150.0  # Liquidates at $59,150
        """
        position_value = position_size * entry_price
        mmr, _ = MarginCalculator.get_maintenance_margin_rate(position_value)
        imr = 1 / leverage  # Initial Margin Rate

        if side.upper() == 'LONG':
            # Long liquidation: price drops
            liq_price = entry_price * (1 - imr + mmr)
        elif side.upper() == 'SHORT':
            # Short liquidation: price rises
            liq_price = entry_price * (1 + imr - mmr)
        else:
            raise ValueError(f"Invalid side: {side}. Must be 'LONG' or 'SHORT'")

        logger.info(f"Liquidation Price ({side}): ${liq_price:.2f} "
                   f"(Entry: ${entry_price:.2f}, Leverage: {leverage}x)")

        return liq_price

    @staticmethod
    def calculate_max_position_size(
        available_balance: float,
        mark_price: float,
        leverage: int,
        max_position_pct: float = 0.10
    ) -> float:
        """
        Calculate maximum safe position size based on available balance

        Args:
            available_balance: Available wallet balance in USDT
            mark_price: Current mark price
            leverage: Desired leverage
            max_position_pct: Maximum % of balance to risk (default 10%)

        Returns:
            Maximum position size in base currency

        Example:
            >>> MarginCalculator.calculate_max_position_size(10000, 65000, 10, 0.10)
            0.1538  # ~0.15 BTC ($10,000 USDT)
        """
        # Max position value = available balance × leverage × position %
        max_position_value = available_balance * leverage * max_position_pct

        # Convert to base currency quantity
        max_position_size = max_position_value / mark_price

        logger.info(f"Max Position Size: {max_position_size:.4f} "
                   f"(Value: ${max_position_value:.2f}, Balance: ${available_balance:.2f}, "
                   f"Leverage: {leverage}x, Risk: {max_position_pct:.1%})")

        return max_position_size

    @staticmethod
    def get_position_summary(
        position_size: float,
        entry_price: float,
        mark_price: float,
        side: str,
        leverage: int,
        wallet_balance: float
    ) -> Dict:
        """
        Get comprehensive position summary with all margin metrics

        Args:
            position_size: Position quantity
            entry_price: Entry price
            mark_price: Current mark price
            side: 'LONG' or 'SHORT'
            leverage: Position leverage
            wallet_balance: Wallet balance

        Returns:
            Dictionary with complete margin analysis
        """
        # Calculate all metrics
        initial_margin = MarginCalculator.calculate_initial_margin(
            position_size, mark_price, leverage
        )

        maintenance_margin, mmr = MarginCalculator.calculate_maintenance_margin(
            position_size, mark_price
        )

        # Calculate unrealized P&L
        position_value = position_size * mark_price
        entry_value = position_size * entry_price
        unrealized_pnl = (position_value - entry_value) if side == 'LONG' else (entry_value - position_value)

        # Margin balance = wallet balance + unrealized P&L
        margin_balance = wallet_balance + unrealized_pnl

        margin_ratio = MarginCalculator.calculate_margin_ratio(
            maintenance_margin, margin_balance
        )

        liquidation_price = MarginCalculator.calculate_liquidation_price(
            entry_price, position_size, side, leverage, wallet_balance
        )

        # Risk assessment
        risk_level = "CRITICAL" if margin_ratio >= 80 else \
                    "HIGH" if margin_ratio >= 50 else \
                    "MEDIUM" if margin_ratio >= 30 else "SAFE"

        return {
            'position_value': position_value,
            'initial_margin': initial_margin,
            'maintenance_margin': maintenance_margin,
            'maintenance_margin_rate': mmr,
            'margin_balance': margin_balance,
            'margin_ratio': margin_ratio,
            'unrealized_pnl': unrealized_pnl,
            'liquidation_price': liquidation_price,
            'risk_level': risk_level,
            'distance_to_liquidation_pct': abs((mark_price - liquidation_price) / mark_price) * 100
        }
