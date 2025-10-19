"""
지원 심볼 및 거래소별 심볼 형식 관리

Features:
- 4개 주요 코인 지원 (BTC, ETH, SOL, ADA)
- 거래소별 심볼 형식 변환
- 심볼 유효성 검증
"""

from typing import Dict, List, Optional
from enum import Enum


class SupportedSymbol(str, Enum):
    """지원되는 심볼"""
    BTC = "BTC"
    ETH = "ETH"
    SOL = "SOL"
    ADA = "ADA"


class SymbolConfig:
    """심볼 설정 및 관리"""

    # 지원 심볼 목록
    SUPPORTED_SYMBOLS = [
        SupportedSymbol.BTC,
        SupportedSymbol.ETH,
        SupportedSymbol.SOL,
        SupportedSymbol.ADA,
    ]

    # 거래소별 심볼 형식
    BINANCE_FORMAT = {
        SupportedSymbol.BTC: "BTCUSDT",
        SupportedSymbol.ETH: "ETHUSDT",
        SupportedSymbol.SOL: "SOLUSDT",
        SupportedSymbol.ADA: "ADAUSDT",
    }

    OKX_FORMAT = {
        SupportedSymbol.BTC: "BTC-USDT-SWAP",
        SupportedSymbol.ETH: "ETH-USDT-SWAP",
        SupportedSymbol.SOL: "SOL-USDT-SWAP",
        SupportedSymbol.ADA: "ADA-USDT-SWAP",
    }

    # 심볼 메타데이터
    SYMBOL_METADATA = {
        SupportedSymbol.BTC: {
            "name": "Bitcoin",
            "category": "Layer 1",
            "min_quantity": 0.001,
            "price_precision": 2,
            "quantity_precision": 3,
        },
        SupportedSymbol.ETH: {
            "name": "Ethereum",
            "category": "Layer 1",
            "min_quantity": 0.01,
            "price_precision": 2,
            "quantity_precision": 3,
        },
        SupportedSymbol.SOL: {
            "name": "Solana",
            "category": "Layer 1",
            "min_quantity": 0.1,
            "price_precision": 3,
            "quantity_precision": 2,
        },
        SupportedSymbol.ADA: {
            "name": "Cardano",
            "category": "Layer 1",
            "min_quantity": 1.0,
            "price_precision": 4,
            "quantity_precision": 1,
        },
    }

    @classmethod
    def get_binance_symbol(cls, symbol: SupportedSymbol) -> str:
        """
        Binance 형식 심볼 반환

        Args:
            symbol: 지원 심볼

        Returns:
            Binance 형식 심볼 (예: BTCUSDT)
        """
        return cls.BINANCE_FORMAT.get(symbol)

    @classmethod
    def get_okx_symbol(cls, symbol: SupportedSymbol) -> str:
        """
        OKX 형식 심볼 반환

        Args:
            symbol: 지원 심볼

        Returns:
            OKX 형식 심볼 (예: BTC-USDT-SWAP)
        """
        return cls.OKX_FORMAT.get(symbol)

    @classmethod
    def validate_symbol(cls, symbol: str, exchange: str = "binance") -> bool:
        """
        심볼 유효성 검증

        Args:
            symbol: 검증할 심볼
            exchange: 거래소 (binance, okx)

        Returns:
            유효 여부
        """
        symbol_upper = symbol.upper()

        if exchange.lower() == "binance":
            return symbol_upper in cls.BINANCE_FORMAT.values()
        elif exchange.lower() == "okx":
            return symbol_upper in cls.OKX_FORMAT.values()
        else:
            return False

    @classmethod
    def parse_symbol(cls, symbol: str, exchange: str = "binance") -> Optional[SupportedSymbol]:
        """
        거래소 형식 심볼을 표준 심볼로 변환

        Args:
            symbol: 거래소 형식 심볼
            exchange: 거래소

        Returns:
            표준 심볼 또는 None
        """
        symbol_upper = symbol.upper()

        if exchange.lower() == "binance":
            for std_symbol, binance_symbol in cls.BINANCE_FORMAT.items():
                if binance_symbol == symbol_upper:
                    return std_symbol
        elif exchange.lower() == "okx":
            for std_symbol, okx_symbol in cls.OKX_FORMAT.items():
                if okx_symbol == symbol_upper:
                    return std_symbol

        return None

    @classmethod
    def get_symbol_info(cls, symbol: SupportedSymbol) -> Dict:
        """
        심볼 메타데이터 반환

        Args:
            symbol: 지원 심볼

        Returns:
            심볼 정보 딕셔너리
        """
        return cls.SYMBOL_METADATA.get(symbol, {})

    @classmethod
    def get_all_symbols_info(cls) -> List[Dict]:
        """
        모든 지원 심볼 정보 반환

        Returns:
            심볼 정보 리스트
        """
        return [
            {
                "symbol": symbol.value,
                "binance": cls.get_binance_symbol(symbol),
                "okx": cls.get_okx_symbol(symbol),
                **cls.get_symbol_info(symbol),
            }
            for symbol in cls.SUPPORTED_SYMBOLS
        ]


# 전역 인스턴스
symbol_config = SymbolConfig()
