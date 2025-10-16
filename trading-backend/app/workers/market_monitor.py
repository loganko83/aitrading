import asyncio
from datetime import datetime
from typing import Dict, List
from app.services.binance import BinanceFuturesClient
from app.ai.ensemble import TripleAIEnsemble
import logging

logger = logging.getLogger(__name__)


class MarketMonitor:
    """
    Background worker for continuous market monitoring

    Responsibilities:
    - Monitor selected symbols for trading opportunities
    - Run AI analysis periodically
    - Detect entry signals
    - Send alerts when conditions are met
    """

    def __init__(self, symbols: List[str], interval: int = 300):
        """
        Initialize market monitor

        Args:
            symbols: List of symbols to monitor (e.g., ["BTCUSDT", "ETHUSDT"])
            interval: Analysis interval in seconds (default: 300 = 5 minutes)
        """
        self.symbols = symbols
        self.interval = interval
        self.binance = BinanceFuturesClient()
        self.ensemble = TripleAIEnsemble()
        self.running = False
        self.tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """Start monitoring all symbols"""
        if self.running:
            logger.warning("Market monitor already running")
            return

        self.running = True
        logger.info(f"Starting market monitor for {len(self.symbols)} symbols")

        # Start monitoring task for each symbol
        for symbol in self.symbols:
            task = asyncio.create_task(self._monitor_symbol(symbol))
            self.tasks[symbol] = task

        logger.info("Market monitor started")

    async def stop(self):
        """Stop monitoring all symbols"""
        if not self.running:
            return

        self.running = False

        # Cancel all monitoring tasks
        for symbol, task in self.tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.tasks.clear()
        logger.info("Market monitor stopped")

    async def _monitor_symbol(self, symbol: str):
        """
        Monitor a single symbol continuously

        Args:
            symbol: Trading pair to monitor
        """
        logger.info(f"Started monitoring {symbol}")

        while self.running:
            try:
                # Fetch market data
                market_data = await self.binance.get_market_data(
                    symbol=symbol,
                    interval="1h",
                    limit=500
                )

                current_price = await self.binance.get_current_price(symbol)

                # Run AI analysis
                decision = await self.ensemble.analyze(
                    symbol=symbol,
                    market_data=market_data,
                    current_price=current_price
                )

                # Log analysis results
                logger.info(
                    f"{symbol} Analysis: {decision.direction} | "
                    f"P={decision.probability_up:.2%} | "
                    f"C={decision.confidence:.2%} | "
                    f"A={decision.agreement:.2%} | "
                    f"Enter={decision.should_enter}"
                )

                # If entry signal detected, send alert
                if decision.should_enter:
                    await self._send_trading_signal(symbol, decision)

                # Wait for next interval
                await asyncio.sleep(self.interval)

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Error monitoring {symbol}: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _send_trading_signal(self, symbol: str, decision):
        """
        Send trading signal when entry conditions are met

        TODO: Implement notification system (email, webhook, database)
        """
        signal = {
            "timestamp": datetime.now().isoformat(),
            "symbol": symbol,
            "direction": decision.direction,
            "probability": decision.probability_up,
            "confidence": decision.confidence,
            "agreement": decision.agreement,
            "entry_price": decision.entry_price,
            "stop_loss": decision.stop_loss,
            "take_profit": decision.take_profit,
            "reasoning": decision.reasoning
        }

        logger.warning(f"🚨 TRADING SIGNAL: {symbol} {decision.direction}")
        logger.info(f"Signal details: {signal}")

        # TODO: Store signal in database
        # TODO: Send notification (email/webhook)
        # TODO: Auto-execute trade if enabled


class PositionManager:
    """
    Background worker for position management

    Responsibilities:
    - Monitor open positions
    - Check for SL/TP hits
    - Detect reversal signals
    - Auto-close positions when needed
    """

    def __init__(self, check_interval: int = 30):
        """
        Initialize position manager

        Args:
            check_interval: Position check interval in seconds (default: 30s)
        """
        self.check_interval = check_interval
        self.binance = BinanceFuturesClient()
        self.ensemble = TripleAIEnsemble()
        self.running = False
        self.task: asyncio.Task = None

    async def start(self):
        """Start position management"""
        if self.running:
            logger.warning("Position manager already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._manage_positions())
        logger.info("Position manager started")

    async def stop(self):
        """Stop position management"""
        if not self.running:
            return

        self.running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Position manager stopped")

    async def _manage_positions(self):
        """Continuously manage open positions"""
        logger.info("Started position management")

        while self.running:
            try:
                # Get all open positions
                positions = await self.binance.get_open_positions()

                if not positions:
                    await asyncio.sleep(self.check_interval)
                    continue

                logger.info(f"Managing {len(positions)} open positions")

                # Check each position
                for position in positions:
                    await self._check_position(position)

                # Wait for next check
                await asyncio.sleep(self.check_interval)

            except asyncio.CancelledError:
                break

            except Exception as e:
                logger.error(f"Error in position management: {e}")
                await asyncio.sleep(60)

    async def _check_position(self, position: Dict):
        """
        Check a single position for management actions

        Args:
            position: Position data from Binance
        """
        symbol = position['symbol']
        side = position['side']
        entry_price = position['entryPrice']
        current_price = position['markPrice']
        unrealized_pnl = position['unrealizedProfit']

        logger.debug(
            f"Checking {symbol} {side}: "
            f"Entry={entry_price:.2f}, "
            f"Current={current_price:.2f}, "
            f"PnL=${unrealized_pnl:.2f}"
        )

        # TODO: Implement position management logic
        # 1. Check if SL/TP should be adjusted
        # 2. Detect reversal signals from AI
        # 3. Auto-close if configured
        # 4. Send alerts for significant P&L changes
