"""
데이터 수집 모듈

Binance API를 통해 과거 OHLCV 데이터를 수집하고 기술적 지표를 추가합니다.

Features:
- Binance Futures 과거 데이터 수집
- 기술적 지표 자동 계산 (RSI, MACD, Bollinger Bands 등)
- 데이터 검증 및 정제
- 캐싱 지원
"""

import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional, List
from binance.client import Client
import ta  # Technical Analysis library

logger = logging.getLogger(__name__)


class MarketDataCollector:
    """
    시장 데이터 수집기

    Features:
    - Binance Futures API를 통한 과거 데이터 수집
    - 기술적 지표 자동 계산
    - 데이터 품질 검증
    """

    def __init__(self, api_key: str = "", api_secret: str = ""):
        """
        Args:
            api_key: Binance API 키 (선택 - 공개 데이터만 사용 시 불필요)
            api_secret: Binance API 시크릿
        """
        self.client = Client(api_key, api_secret)

    def fetch_historical_data(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        days: int = 365,
        end_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        과거 OHLCV 데이터 수집

        Args:
            symbol: 거래 심볼 (예: BTCUSDT)
            interval: 캔들 간격 (1m, 5m, 15m, 1h, 4h, 1d)
            days: 수집할 일수
            end_date: 종료 날짜 (None이면 현재)

        Returns:
            OHLCV 데이터프레임 (timestamp, open, high, low, close, volume)
        """
        logger.info(f"Fetching {days} days of {symbol} {interval} data from Binance...")

        # 종료 날짜 설정
        if end_date is None:
            end_date = datetime.now()

        # 시작 날짜 계산
        start_date = end_date - timedelta(days=days)

        # Binance API 호출
        try:
            klines = self.client.futures_historical_klines(
                symbol=symbol,
                interval=interval,
                start_str=start_date.strftime("%Y-%m-%d"),
                end_str=end_date.strftime("%Y-%m-%d")
            )

            # 데이터프레임 변환
            df = pd.DataFrame(klines, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_volume', 'trades', 'taker_buy_base',
                'taker_buy_quote', 'ignore'
            ])

            # 필요한 컬럼만 선택
            df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]

            # 타임스탬프를 datetime으로 변환
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            # 숫자 타입으로 변환
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 결측치 제거
            df = df.dropna()

            logger.info(f"✅ Collected {len(df)} candles from {df['timestamp'].min()} to {df['timestamp'].max()}")

            return df

        except Exception as e:
            logger.error(f"Failed to fetch historical data: {e}")
            raise

    def add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        기술적 지표 추가

        추가되는 지표:
        - RSI (14)
        - MACD (12, 26, 9)
        - Bollinger Bands (20, 2)
        - EMA (9, 21, 50)
        - ATR (14)
        - Volume Moving Average (20)

        Args:
            df: OHLCV 데이터프레임

        Returns:
            기술적 지표가 추가된 데이터프레임
        """
        logger.info("Adding technical indicators...")

        df = df.copy()

        # RSI (Relative Strength Index)
        df['rsi'] = ta.momentum.RSIIndicator(
            close=df['close'],
            window=14
        ).rsi()

        # MACD (Moving Average Convergence Divergence)
        macd = ta.trend.MACD(
            close=df['close'],
            window_slow=26,
            window_fast=12,
            window_sign=9
        )
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['macd_diff'] = macd.macd_diff()

        # Bollinger Bands
        bollinger = ta.volatility.BollingerBands(
            close=df['close'],
            window=20,
            window_dev=2
        )
        df['bb_high'] = bollinger.bollinger_hband()
        df['bb_mid'] = bollinger.bollinger_mavg()
        df['bb_low'] = bollinger.bollinger_lband()
        df['bb_width'] = bollinger.bollinger_wband()

        # EMA (Exponential Moving Averages)
        df['ema_9'] = ta.trend.EMAIndicator(close=df['close'], window=9).ema_indicator()
        df['ema_21'] = ta.trend.EMAIndicator(close=df['close'], window=21).ema_indicator()
        df['ema_50'] = ta.trend.EMAIndicator(close=df['close'], window=50).ema_indicator()

        # ATR (Average True Range)
        df['atr'] = ta.volatility.AverageTrueRange(
            high=df['high'],
            low=df['low'],
            close=df['close'],
            window=14
        ).average_true_range()

        # Volume Moving Average
        df['volume_ma'] = df['volume'].rolling(window=20).mean()

        # Price Change Percentage
        df['price_change_pct'] = df['close'].pct_change() * 100

        # Volume Change Percentage
        df['volume_change_pct'] = df['volume'].pct_change() * 100

        # 결측치 제거 (초기 지표 계산 시 발생)
        df = df.dropna()

        logger.info(f"✅ Added {len(df.columns) - 6} technical indicators")

        return df

    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        데이터 품질 검증

        Args:
            df: 데이터프레임

        Returns:
            검증 통과 여부
        """
        # 최소 데이터 개수 확인
        if len(df) < 100:
            logger.error(f"Insufficient data: {len(df)} rows (minimum: 100)")
            return False

        # 결측치 확인
        if df.isnull().any().any():
            logger.error("Data contains null values")
            return False

        # OHLC 관계 검증
        invalid_ohlc = (
            (df['high'] < df['low']) |
            (df['close'] > df['high']) |
            (df['close'] < df['low']) |
            (df['open'] > df['high']) |
            (df['open'] < df['low'])
        ).any()

        if invalid_ohlc:
            logger.error("Invalid OHLC relationships detected")
            return False

        # 볼륨 양수 확인
        if (df['volume'] <= 0).any():
            logger.error("Negative or zero volume detected")
            return False

        logger.info("✅ Data validation passed")
        return True

    def prepare_dataset(
        self,
        symbol: str = "BTCUSDT",
        interval: str = "1h",
        days: int = 365
    ) -> pd.DataFrame:
        """
        LSTM 모델용 완전한 데이터셋 준비

        Args:
            symbol: 거래 심볼
            interval: 캔들 간격
            days: 수집할 일수

        Returns:
            기술적 지표가 포함된 검증된 데이터셋
        """
        # 1. 데이터 수집
        df = self.fetch_historical_data(
            symbol=symbol,
            interval=interval,
            days=days
        )

        # 2. 기술적 지표 추가
        df = self.add_technical_indicators(df)

        # 3. 데이터 검증
        if not self.validate_data(df):
            raise ValueError("Data validation failed")

        # 4. 인덱스 설정
        df = df.set_index('timestamp')

        logger.info(
            f"✅ Dataset prepared: {len(df)} samples, {len(df.columns)} features\n"
            f"   Period: {df.index.min()} to {df.index.max()}\n"
            f"   Features: {list(df.columns)}"
        )

        return df


# =======================
# 사용 예시
# =======================

if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)

    # 데이터 수집기 생성
    collector = MarketDataCollector()

    # BTCUSDT 1년치 1시간봉 데이터 수집
    df = collector.prepare_dataset(
        symbol="BTCUSDT",
        interval="1h",
        days=365
    )

    print("\n데이터셋 정보:")
    print(df.info())
    print("\n데이터셋 샘플:")
    print(df.head())
    print("\n기술적 지표 통계:")
    print(df.describe())
