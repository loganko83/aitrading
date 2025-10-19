"""
실시간 시장 데이터 API

Features:
- 4개 코인 실시간 가격 조회
- 24시간 통계 조회
- 멀티 거래소 지원 (Binance, OKX)
- Redis 캐싱으로 성능 최적화
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.core.symbols import symbol_config, SupportedSymbol
from app.services.binance_client import BinanceClient
from app.services.okx_client import OKXClient
from app.core.redis_client import cached

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["market"])


# 캐싱 헬퍼 함수들
@cached(ttl=5, key_prefix="market:prices")
async def _fetch_prices_cached(exchange: str, symbols_str: str):
    """가격 조회 캐싱 (5초 TTL)"""
    symbol_list = [s.strip().upper() for s in symbols_str.split(",")]
    target_symbols = [SupportedSymbol(s) for s in symbol_list]

    prices = []
    import time
    current_timestamp = int(time.time() * 1000)

    if exchange == "binance":
        client = BinanceClient(api_key="", api_secret="", testnet=False)
        for symbol in target_symbols:
            try:
                exchange_symbol = symbol_config.get_binance_symbol(symbol)
                price = client.get_current_price(exchange_symbol)
                prices.append({
                    "symbol": symbol.value,
                    "exchange": "binance",
                    "price": price,
                    "timestamp": current_timestamp
                })
            except Exception as e:
                logger.error(f"Failed to get price for {symbol.value}: {str(e)}")
                continue

    elif exchange == "okx":
        client = OKXClient(api_key="", api_secret="", passphrase="", testnet=False)
        for symbol in target_symbols:
            try:
                exchange_symbol = symbol_config.get_okx_symbol(symbol)
                price = client.get_current_price(exchange_symbol)
                prices.append({
                    "symbol": symbol.value,
                    "exchange": "okx",
                    "price": price,
                    "timestamp": current_timestamp
                })
            except Exception as e:
                logger.error(f"Failed to get price for {symbol.value}: {str(e)}")
                continue

    return prices


@cached(ttl=60, key_prefix="market:24h_stats")
async def _fetch_24h_stats_cached(exchange: str, symbols_str: str):
    """24시간 통계 조회 캐싱 (60초 TTL)"""
    symbol_list = [s.strip().upper() for s in symbols_str.split(",")]
    target_symbols = [SupportedSymbol(s) for s in symbol_list]

    tickers = []

    if exchange == "binance":
        client = BinanceClient(api_key="", api_secret="", testnet=False)
        for symbol in target_symbols:
            try:
                exchange_symbol = symbol_config.get_binance_symbol(symbol)
                ticker_data = client.get_24h_ticker(exchange_symbol)
                tickers.append({
                    "symbol": symbol.value,
                    "exchange": "binance",
                    **ticker_data
                })
            except Exception as e:
                logger.error(f"Failed to get 24h ticker for {symbol.value}: {str(e)}")
                continue

    elif exchange == "okx":
        client = OKXClient(api_key="", api_secret="", passphrase="", testnet=False)
        for symbol in target_symbols:
            try:
                exchange_symbol = symbol_config.get_okx_symbol(symbol)
                ticker_data = client.get_24h_ticker(exchange_symbol)
                tickers.append({
                    "symbol": symbol.value,
                    "exchange": "okx",
                    **ticker_data
                })
            except Exception as e:
                logger.error(f"Failed to get 24h ticker for {symbol.value}: {str(e)}")
                continue

    return tickers


@cached(ttl=3, key_prefix="market:price")
async def _fetch_single_price_cached(symbol: str, exchange: str):
    """단일 심볼 가격 조회 캐싱 (3초 TTL)"""
    import time
    current_timestamp = int(time.time() * 1000)

    std_symbol = SupportedSymbol(symbol)

    if exchange == "binance":
        client = BinanceClient(api_key="", api_secret="", testnet=False)
        exchange_symbol = symbol_config.get_binance_symbol(std_symbol)
        price = client.get_current_price(exchange_symbol)

    elif exchange == "okx":
        client = OKXClient(api_key="", api_secret="", passphrase="", testnet=False)
        exchange_symbol = symbol_config.get_okx_symbol(std_symbol)
        price = client.get_current_price(exchange_symbol)

    return {
        "symbol": symbol,
        "exchange": exchange,
        "price": price,
        "timestamp": current_timestamp
    }


class PriceData(BaseModel):
    """가격 데이터"""
    symbol: str
    exchange: str
    price: float
    timestamp: int


class TickerData(BaseModel):
    """24시간 통계 데이터"""
    symbol: str
    exchange: str
    price_change: float
    price_change_percent: float
    last_price: float
    high_price: float
    low_price: float
    volume: float
    quote_volume: float
    open_time: int
    close_time: int
    count: int


class MultiSymbolPriceResponse(BaseModel):
    """멀티 심볼 가격 응답"""
    prices: List[PriceData]
    total: int


class MultiSymbolTickerResponse(BaseModel):
    """멀티 심볼 24시간 통계 응답"""
    tickers: List[TickerData]
    total: int


@router.get("/prices", response_model=MultiSymbolPriceResponse)
async def get_multi_symbol_prices(
    exchange: str = "binance",
    symbols: Optional[str] = None
):
    """
    4개 코인 실시간 가격 조회 (Redis 캐싱: 5초 TTL)

    **파라미터**:
    - exchange: 거래소 (binance, okx)
    - symbols: 심볼 목록 (쉼표 구분, 미지정시 전체)

    **응답**:
    - prices: 가격 데이터 목록
    - total: 총 개수

    **예시**:
    - GET /api/v1/market/prices?exchange=binance
    - GET /api/v1/market/prices?exchange=okx&symbols=BTC,ETH

    **성능**: 캐싱으로 5초 내 동일 요청은 즉시 응답 (< 1ms)
    """
    try:
        exchange_lower = exchange.lower()
        if exchange_lower not in ["binance", "okx"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported exchange: {exchange}"
            )

        # 심볼 목록 결정
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            # 지원 심볼인지 검증
            supported_symbols = [s.value for s in symbol_config.SUPPORTED_SYMBOLS]
            for sym in symbol_list:
                if sym not in supported_symbols:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported symbol: {sym}. Supported: {', '.join(supported_symbols)}"
                    )
            symbols_str = ",".join(symbol_list)
        else:
            # 전체 지원 심볼
            symbols_str = ",".join([s.value for s in symbol_config.SUPPORTED_SYMBOLS])

        # 캐싱된 헬퍼 함수 호출
        prices_data = await _fetch_prices_cached(exchange_lower, symbols_str)

        # Pydantic 모델로 변환
        prices = [PriceData(**p) for p in prices_data]

        return MultiSymbolPriceResponse(
            prices=prices,
            total=len(prices)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get multi-symbol prices: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get prices: {str(e)}"
        )


@router.get("/24h-stats", response_model=MultiSymbolTickerResponse)
async def get_24h_stats(
    exchange: str = "binance",
    symbols: Optional[str] = None
):
    """
    4개 코인 24시간 통계 조회 (Redis 캐싱: 60초 TTL)

    **파라미터**:
    - exchange: 거래소 (binance, okx)
    - symbols: 심볼 목록 (쉼표 구분, 미지정시 전체)

    **응답**:
    - tickers: 24시간 통계 데이터 목록
    - total: 총 개수

    **예시**:
    - GET /api/v1/market/24h-stats?exchange=binance
    - GET /api/v1/market/24h-stats?exchange=okx&symbols=BTC,ETH,SOL

    **성능**: 캐싱으로 60초 내 동일 요청은 즉시 응답 (< 1ms)
    """
    try:
        exchange_lower = exchange.lower()
        if exchange_lower not in ["binance", "okx"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported exchange: {exchange}"
            )

        # 심볼 목록 결정
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            # 지원 심볼인지 검증
            supported_symbols = [s.value for s in symbol_config.SUPPORTED_SYMBOLS]
            for sym in symbol_list:
                if sym not in supported_symbols:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported symbol: {sym}. Supported: {', '.join(supported_symbols)}"
                    )
            symbols_str = ",".join(symbol_list)
        else:
            # 전체 지원 심볼
            symbols_str = ",".join([s.value for s in symbol_config.SUPPORTED_SYMBOLS])

        # 캐싱된 헬퍼 함수 호출
        tickers_data = await _fetch_24h_stats_cached(exchange_lower, symbols_str)

        # Pydantic 모델로 변환
        tickers = [TickerData(**t) for t in tickers_data]

        return MultiSymbolTickerResponse(
            tickers=tickers,
            total=len(tickers)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get 24h stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get 24h stats: {str(e)}"
        )


@router.get("/price/{symbol}")
async def get_single_price(
    symbol: str,
    exchange: str = "binance"
):
    """
    단일 심볼 가격 조회 (Redis 캐싱: 3초 TTL)

    **파라미터**:
    - symbol: 심볼 (BTC, ETH, SOL, ADA)
    - exchange: 거래소 (binance, okx)

    **응답**:
    - symbol: 심볼
    - exchange: 거래소
    - price: 현재 가격
    - timestamp: 타임스탬프

    **예시**:
    - GET /api/v1/market/price/BTC?exchange=binance

    **성능**: 캐싱으로 3초 내 동일 요청은 즉시 응답 (< 1ms)
    """
    try:
        symbol_upper = symbol.upper()
        exchange_lower = exchange.lower()

        # 심볼 검증
        try:
            std_symbol = SupportedSymbol(symbol_upper)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported symbol: {symbol_upper}"
            )

        # 거래소 검증
        if exchange_lower not in ["binance", "okx"]:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported exchange: {exchange}"
            )

        # 캐싱된 헬퍼 함수 호출
        result = await _fetch_single_price_cached(symbol_upper, exchange_lower)

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get price for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get price: {str(e)}"
        )
