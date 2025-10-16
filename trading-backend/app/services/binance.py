from binance.client import Client
from binance.exceptions import BinanceAPIException
from typing import Dict, List, Optional
import pandas as pd
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class BinanceFuturesClient:
    """Binance Futures API Client for trading operations"""

    def __init__(self, api_key: str = None, api_secret: str = None, testnet: bool = None):
        """
        Initialize Binance Futures client

        Args:
            api_key: Binance API key (defaults to settings)
            api_secret: Binance API secret (defaults to settings)
            testnet: Use testnet or mainnet (defaults to settings)
        """
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_API_SECRET
        self.testnet = testnet if testnet is not None else settings.BINANCE_TESTNET

        # Initialize client
        if self.testnet:
            self.client = Client(
                api_key=self.api_key,
                api_secret=self.api_secret,
                testnet=True
            )
        else:
            self.client = Client(
                api_key=self.api_key,
                api_secret=self.api_secret
            )

        logger.info(f"Binance Futures client initialized (testnet={self.testnet})")

    async def get_account_balance(self) -> Dict:
        """
        Get futures account balance

        Returns:
            Account balance information including USDT balance
        """
        try:
            account = self.client.futures_account()

            # Extract USDT balance
            usdt_balance = next(
                (asset for asset in account['assets'] if asset['asset'] == 'USDT'),
                None
            )

            return {
                'totalWalletBalance': float(account['totalWalletBalance']),
                'totalUnrealizedProfit': float(account['totalUnrealizedProfit']),
                'totalMarginBalance': float(account['totalMarginBalance']),
                'availableBalance': float(account['availableBalance']),
                'maxWithdrawAmount': float(account['maxWithdrawAmount']),
                'usdt': {
                    'balance': float(usdt_balance['walletBalance']) if usdt_balance else 0,
                    'unrealizedProfit': float(usdt_balance['unrealizedProfit']) if usdt_balance else 0,
                    'available': float(usdt_balance['availableBalance']) if usdt_balance else 0
                }
            }
        except BinanceAPIException as e:
            logger.error(f"Error fetching account balance: {e}")
            raise

    async def get_market_data(self, symbol: str, interval: str = '1h', limit: int = 500) -> pd.DataFrame:
        """
        Fetch historical OHLCV data for a symbol

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            interval: Kline interval (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles to fetch (max 1500)

        Returns:
            DataFrame with columns: timestamp, open, high, low, close, volume
        """
        try:
            klines = self.client.futures_klines(
                symbol=symbol,
                interval=interval,
                limit=limit
            )

            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # Convert to appropriate types
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = df[col].astype(float)

            # Keep only relevant columns
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

            return df
        except BinanceAPIException as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            raise

    async def get_current_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')

        Returns:
            Current price as float
        """
        try:
            ticker = self.client.futures_symbol_ticker(symbol=symbol)
            return float(ticker['price'])
        except BinanceAPIException as e:
            logger.error(f"Error fetching price for {symbol}: {e}")
            raise

    async def get_open_positions(self) -> List[Dict]:
        """
        Get all open positions

        Returns:
            List of open positions with details
        """
        try:
            positions = self.client.futures_position_information()

            # Filter only positions with non-zero size
            open_positions = []
            for pos in positions:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    open_positions.append({
                        'symbol': pos['symbol'],
                        'side': 'LONG' if position_amt > 0 else 'SHORT',
                        'quantity': abs(position_amt),
                        'entryPrice': float(pos['entryPrice']),
                        'markPrice': float(pos['markPrice']),
                        'unrealizedProfit': float(pos['unrealizedProfit']),
                        'leverage': int(pos['leverage']),
                        'liquidationPrice': float(pos['liquidationPrice']),
                    })

            return open_positions
        except BinanceAPIException as e:
            logger.error(f"Error fetching open positions: {e}")
            raise

    async def place_market_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        reduce_only: bool = False
    ) -> Dict:
        """
        Place a market order

        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            reduce_only: If True, order can only reduce position

        Returns:
            Order information
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='MARKET',
                quantity=quantity,
                reduceOnly=reduce_only
            )

            logger.info(f"Market order placed: {symbol} {side} {quantity}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error placing market order: {e}")
            raise

    async def place_limit_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        price: float,
        time_in_force: str = 'GTC'
    ) -> Dict:
        """
        Place a limit order

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Limit price
            time_in_force: GTC (Good Till Cancel), IOC (Immediate or Cancel), FOK (Fill or Kill)

        Returns:
            Order information
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='LIMIT',
                quantity=quantity,
                price=price,
                timeInForce=time_in_force
            )

            logger.info(f"Limit order placed: {symbol} {side} {quantity} @ {price}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error placing limit order: {e}")
            raise

    async def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """
        Set leverage for a symbol

        Args:
            symbol: Trading pair
            leverage: Leverage value (1-125)

        Returns:
            Leverage change confirmation
        """
        try:
            result = self.client.futures_change_leverage(
                symbol=symbol,
                leverage=leverage
            )
            logger.info(f"Leverage set to {leverage}x for {symbol}")
            return result
        except BinanceAPIException as e:
            logger.error(f"Error setting leverage: {e}")
            raise

    async def set_stop_loss(
        self,
        symbol: str,
        side: str,
        quantity: float,
        stop_price: float
    ) -> Dict:
        """
        Set stop-loss order

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL' (opposite of position)
            quantity: Position quantity to close
            stop_price: Stop-loss trigger price

        Returns:
            Stop order information
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='STOP_MARKET',
                stopPrice=stop_price,
                quantity=quantity,
                reduceOnly=True
            )

            logger.info(f"Stop-loss set: {symbol} @ {stop_price}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error setting stop-loss: {e}")
            raise

    async def set_take_profit(
        self,
        symbol: str,
        side: str,
        quantity: float,
        take_profit_price: float
    ) -> Dict:
        """
        Set take-profit order

        Args:
            symbol: Trading pair
            side: 'BUY' or 'SELL' (opposite of position)
            quantity: Position quantity to close
            take_profit_price: Take-profit trigger price

        Returns:
            Take-profit order information
        """
        try:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=side,
                type='TAKE_PROFIT_MARKET',
                stopPrice=take_profit_price,
                quantity=quantity,
                reduceOnly=True
            )

            logger.info(f"Take-profit set: {symbol} @ {take_profit_price}")
            return order
        except BinanceAPIException as e:
            logger.error(f"Error setting take-profit: {e}")
            raise

    async def close_position(self, symbol: str, quantity: float = None) -> Dict:
        """
        Close an open position

        Args:
            symbol: Trading pair
            quantity: Position quantity to close (None = close all)

        Returns:
            Close order information
        """
        try:
            # Get current position
            positions = await self.get_open_positions()
            position = next((p for p in positions if p['symbol'] == symbol), None)

            if not position:
                raise ValueError(f"No open position found for {symbol}")

            # Determine close side (opposite of position)
            close_side = 'SELL' if position['side'] == 'LONG' else 'BUY'
            close_quantity = quantity or position['quantity']

            # Place market order to close
            order = await self.place_market_order(
                symbol=symbol,
                side=close_side,
                quantity=close_quantity,
                reduce_only=True
            )

            logger.info(f"Position closed: {symbol} {close_quantity}")
            return order
        except Exception as e:
            logger.error(f"Error closing position: {e}")
            raise
