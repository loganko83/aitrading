"""
심볼 관리 API

Features:
- 지원 심볼 목록 조회
- 거래소별 심볼 형식 변환
- 심볼 메타데이터 제공
"""

from fastapi import APIRouter
from typing import List, Dict
from pydantic import BaseModel

from app.core.symbols import symbol_config, SupportedSymbol

router = APIRouter(prefix="/symbols", tags=["Symbols"])


class SymbolInfo(BaseModel):
    """심볼 정보"""
    symbol: str
    name: str
    category: str
    binance: str
    okx: str
    min_quantity: float
    price_precision: int
    quantity_precision: int


class SymbolListResponse(BaseModel):
    """심볼 목록 응답"""
    symbols: List[SymbolInfo]
    total: int


@router.get("/list", response_model=SymbolListResponse)
async def get_supported_symbols():
    """
    지원 심볼 목록 조회

    **지원 심볼**: BTC, ETH, SOL, ADA

    **응답 정보**:
    - symbol: 표준 심볼 (BTC, ETH, ...)
    - name: 풀네임 (Bitcoin, Ethereum, ...)
    - category: 카테고리 (Layer 1, ...)
    - binance: Binance 형식 (BTCUSDT, ...)
    - okx: OKX 형식 (BTC-USDT-SWAP, ...)
    - min_quantity: 최소 주문 수량
    - price_precision: 가격 소수점 자리수
    - quantity_precision: 수량 소수점 자리수
    """
    all_symbols = symbol_config.get_all_symbols_info()

    symbols = [
        SymbolInfo(
            symbol=s["symbol"],
            name=s["name"],
            category=s["category"],
            binance=s["binance"],
            okx=s["okx"],
            min_quantity=s["min_quantity"],
            price_precision=s["price_precision"],
            quantity_precision=s["quantity_precision"]
        )
        for s in all_symbols
    ]

    return SymbolListResponse(
        symbols=symbols,
        total=len(symbols)
    )


@router.get("/{symbol}")
async def get_symbol_info(symbol: str):
    """
    특정 심볼 정보 조회

    **파라미터**:
    - symbol: 심볼 (BTC, ETH, SOL, ADA)

    **응답**:
    - 심볼 메타데이터
    - 거래소별 형식
    """
    try:
        std_symbol = SupportedSymbol(symbol.upper())
    except ValueError:
        return {
            "error": f"Unsupported symbol: {symbol}",
            "supported": [s.value for s in symbol_config.SUPPORTED_SYMBOLS]
        }

    info = symbol_config.get_symbol_info(std_symbol)

    return {
        "symbol": std_symbol.value,
        "binance": symbol_config.get_binance_symbol(std_symbol),
        "okx": symbol_config.get_okx_symbol(std_symbol),
        **info
    }


@router.get("/convert/{symbol}")
async def convert_symbol(symbol: str, exchange: str = "binance"):
    """
    심볼 형식 변환

    **파라미터**:
    - symbol: 표준 심볼 (BTC, ETH, ...)
    - exchange: 거래소 (binance, okx)

    **응답**:
    - converted: 거래소 형식 심볼
    """
    try:
        std_symbol = SupportedSymbol(symbol.upper())
    except ValueError:
        return {
            "error": f"Unsupported symbol: {symbol}",
            "supported": [s.value for s in symbol_config.SUPPORTED_SYMBOLS]
        }

    if exchange.lower() == "binance":
        converted = symbol_config.get_binance_symbol(std_symbol)
    elif exchange.lower() == "okx":
        converted = symbol_config.get_okx_symbol(std_symbol)
    else:
        return {"error": f"Unsupported exchange: {exchange}"}

    return {
        "original": std_symbol.value,
        "exchange": exchange.lower(),
        "converted": converted
    }
