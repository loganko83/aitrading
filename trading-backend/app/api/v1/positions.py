"""
포지션 관리 API

Features:
- 멀티 심볼 포지션 조회
- 포트폴리오 요약
- 전체 포지션 일괄 청산
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from app.core.symbols import symbol_config, SupportedSymbol
from app.services.order_executor import order_executor, Exchange
from app.services.binance_client import BinanceClient
from app.services.okx_client import OKXClient
from app.core.crypto import crypto_service
from app.database.session import get_db
from sqlalchemy.orm import Session
from app.models.api_key import ApiKey

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/positions", tags=["positions"])


class PositionData(BaseModel):
    """포지션 데이터"""
    symbol: str
    exchange: str
    account_id: str
    position_amt: float
    entry_price: float
    unrealized_pnl: float
    leverage: int
    side: str


class PortfolioSummary(BaseModel):
    """포트폴리오 요약"""
    total_balance: float
    total_unrealized_pnl: float
    total_positions: int
    positions_by_symbol: Dict[str, int]
    positions_by_exchange: Dict[str, int]
    accounts: List[Dict[str, Any]]


class MultiSymbolPositionsResponse(BaseModel):
    """멀티 심볼 포지션 응답"""
    positions: List[PositionData]
    total: int
    summary: Dict[str, Any]


class CloseAllResponse(BaseModel):
    """전체 청산 응답"""
    success: bool
    closed_positions: int
    failed_positions: int
    results: List[Dict[str, Any]]


@router.get("/multi-symbol", response_model=MultiSymbolPositionsResponse)
async def get_multi_symbol_positions(
    account_ids: Optional[str] = None,
    symbols: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    멀티 심볼 포지션 조회

    **파라미터**:
    - account_ids: 계정 ID 목록 (쉼표 구분, 미지정시 전체)
    - symbols: 심볼 목록 (쉼표 구분, 미지정시 전체)

    **응답**:
    - positions: 포지션 목록
    - total: 총 포지션 수
    - summary: 요약 정보

    **예시**:
    - GET /api/v1/positions/multi-symbol
    - GET /api/v1/positions/multi-symbol?symbols=BTC,ETH
    """
    try:
        # 계정 ID 목록 결정
        if account_ids:
            target_account_ids = [aid.strip() for aid in account_ids.split(",")]
        else:
            # DB에서 모든 활성 계정 조회
            all_accounts = db.query(ApiKey).filter(ApiKey.is_active == True).all()
            target_account_ids = [acc.id for acc in all_accounts]

        # 심볼 목록 결정
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            target_symbols = [SupportedSymbol(s) for s in symbol_list if s in [sym.value for sym in symbol_config.SUPPORTED_SYMBOLS]]
        else:
            target_symbols = symbol_config.SUPPORTED_SYMBOLS

        all_positions = []
        total_unrealized_pnl = 0.0
        positions_by_symbol = {}
        positions_by_exchange = {}

        # 각 계정별 포지션 조회
        for account_id in target_account_ids:
            # 계정 정보 조회
            account = db.query(ApiKey).filter(ApiKey.id == account_id).first()
            if not account or not account.is_active:
                logger.warning(f"Account {account_id} not found or inactive")
                continue

            # API 키 복호화
            try:
                decrypted_creds = crypto_service.decrypt_api_credentials({
                    "api_key": account.api_key,
                    "api_secret": account.api_secret,
                    "passphrase": account.passphrase
                })
            except Exception as e:
                logger.error(f"Failed to decrypt credentials for {account_id}: {str(e)}")
                continue

            # 거래소별 클라이언트 생성
            exchange_lower = account.exchange.lower()

            try:
                if exchange_lower == "binance":
                    client = BinanceClient(
                        api_key=decrypted_creds["api_key"],
                        api_secret=decrypted_creds["api_secret"],
                        testnet=account.testnet
                    )

                    # 각 심볼별 포지션 조회
                    for symbol in target_symbols:
                        exchange_symbol = symbol_config.get_binance_symbol(symbol)
                        positions = client.get_positions(exchange_symbol)

                        for pos in positions:
                            all_positions.append(PositionData(
                                symbol=symbol.value,
                                exchange="binance",
                                account_id=account_id,
                                position_amt=pos["position_amt"],
                                entry_price=pos["entry_price"],
                                unrealized_pnl=pos["unrealized_pnl"],
                                leverage=pos["leverage"],
                                side=pos["side"]
                            ))

                            total_unrealized_pnl += pos["unrealized_pnl"]

                            # 집계
                            positions_by_symbol[symbol.value] = positions_by_symbol.get(symbol.value, 0) + 1
                            positions_by_exchange["binance"] = positions_by_exchange.get("binance", 0) + 1

                elif exchange_lower == "okx":
                    client = OKXClient(
                        api_key=decrypted_creds["api_key"],
                        api_secret=decrypted_creds["api_secret"],
                        passphrase=decrypted_creds["passphrase"],
                        testnet=account.testnet
                    )

                    # 각 심볼별 포지션 조회
                    for symbol in target_symbols:
                        exchange_symbol = symbol_config.get_okx_symbol(symbol)
                        positions = client.get_positions(exchange_symbol)

                        for pos in positions:
                            all_positions.append(PositionData(
                                symbol=symbol.value,
                                exchange="okx",
                                account_id=account_id,
                                position_amt=pos["position_amt"],
                                entry_price=pos["entry_price"],
                                unrealized_pnl=pos["unrealized_pnl"],
                                leverage=pos["leverage"],
                                side=pos["side"]
                            ))

                            total_unrealized_pnl += pos["unrealized_pnl"]

                            # 집계
                            positions_by_symbol[symbol.value] = positions_by_symbol.get(symbol.value, 0) + 1
                            positions_by_exchange["okx"] = positions_by_exchange.get("okx", 0) + 1

            except Exception as e:
                logger.error(f"Failed to get positions for {account_id}: {str(e)}")
                continue

        return MultiSymbolPositionsResponse(
            positions=all_positions,
            total=len(all_positions),
            summary={
                "total_unrealized_pnl": round(total_unrealized_pnl, 2),
                "positions_by_symbol": positions_by_symbol,
                "positions_by_exchange": positions_by_exchange
            }
        )

    except Exception as e:
        logger.error(f"Failed to get multi-symbol positions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get positions: {str(e)}"
        )


@router.get("/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    account_ids: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    포트폴리오 요약 조회

    **파라미터**:
    - account_ids: 계정 ID 목록 (쉼표 구분, 미지정시 전체)

    **응답**:
    - total_balance: 총 잔액 (USDT)
    - total_unrealized_pnl: 총 미실현 손익
    - total_positions: 총 포지션 수
    - positions_by_symbol: 심볼별 포지션 수
    - positions_by_exchange: 거래소별 포지션 수
    - accounts: 계정별 상세 정보

    **예시**:
    - GET /api/v1/positions/summary
    """
    try:
        # 계정 ID 목록 결정
        if account_ids:
            target_account_ids = [aid.strip() for aid in account_ids.split(",")]
        else:
            # DB에서 모든 활성 계정 조회
            all_accounts = db.query(ApiKey).filter(ApiKey.is_active == True).all()
            target_account_ids = [acc.id for acc in all_accounts]

        total_balance = 0.0
        total_unrealized_pnl = 0.0
        total_positions = 0
        positions_by_symbol = {}
        positions_by_exchange = {}
        account_details = []

        # 각 계정별 정보 수집
        for account_id in target_account_ids:
            # 계정 정보 조회
            account = db.query(ApiKey).filter(ApiKey.id == account_id).first()
            if not account or not account.is_active:
                continue

            # API 키 복호화
            try:
                decrypted_creds = crypto_service.decrypt_api_credentials({
                    "api_key": account.api_key,
                    "api_secret": account.api_secret,
                    "passphrase": account.passphrase
                })
            except Exception as e:
                logger.error(f"Failed to decrypt credentials for {account_id}: {str(e)}")
                continue

            exchange_lower = account.exchange.lower()

            try:
                if exchange_lower == "binance":
                    client = BinanceClient(
                        api_key=decrypted_creds["api_key"],
                        api_secret=decrypted_creds["api_secret"],
                        testnet=account.testnet
                    )

                    # 잔액 조회
                    balance_info = client.get_account_balance()
                    account_balance = balance_info["total_balance"]

                    # 포지션 조회
                    positions = client.get_positions()
                    account_positions = len(positions)
                    account_pnl = sum([pos["unrealized_pnl"] for pos in positions])

                    # 집계
                    total_balance += account_balance
                    total_unrealized_pnl += account_pnl
                    total_positions += account_positions

                    for pos in positions:
                        # 심볼 파싱
                        std_symbol = symbol_config.parse_symbol(pos["symbol"], "binance")
                        if std_symbol:
                            positions_by_symbol[std_symbol.value] = positions_by_symbol.get(std_symbol.value, 0) + 1

                    positions_by_exchange["binance"] = positions_by_exchange.get("binance", 0) + account_positions

                    account_details.append({
                        "account_id": account_id,
                        "exchange": "binance",
                        "balance": account_balance,
                        "unrealized_pnl": account_pnl,
                        "positions": account_positions,
                        "testnet": account.testnet
                    })

                elif exchange_lower == "okx":
                    client = OKXClient(
                        api_key=decrypted_creds["api_key"],
                        api_secret=decrypted_creds["api_secret"],
                        passphrase=decrypted_creds["passphrase"],
                        testnet=account.testnet
                    )

                    # 잔액 조회
                    balance_info = client.get_account_balance()
                    account_balance = balance_info["total_balance"]

                    # 포지션 조회
                    positions = client.get_positions()
                    account_positions = len(positions)
                    account_pnl = sum([pos["unrealized_pnl"] for pos in positions])

                    # 집계
                    total_balance += account_balance
                    total_unrealized_pnl += account_pnl
                    total_positions += account_positions

                    for pos in positions:
                        # 심볼 파싱
                        std_symbol = symbol_config.parse_symbol(pos["symbol"], "okx")
                        if std_symbol:
                            positions_by_symbol[std_symbol.value] = positions_by_symbol.get(std_symbol.value, 0) + 1

                    positions_by_exchange["okx"] = positions_by_exchange.get("okx", 0) + account_positions

                    account_details.append({
                        "account_id": account_id,
                        "exchange": "okx",
                        "balance": account_balance,
                        "unrealized_pnl": account_pnl,
                        "positions": account_positions,
                        "testnet": account.testnet
                    })

            except Exception as e:
                logger.error(f"Failed to get summary for {account_id}: {str(e)}")
                continue

        return PortfolioSummary(
            total_balance=round(total_balance, 2),
            total_unrealized_pnl=round(total_unrealized_pnl, 2),
            total_positions=total_positions,
            positions_by_symbol=positions_by_symbol,
            positions_by_exchange=positions_by_exchange,
            accounts=account_details
        )

    except Exception as e:
        logger.error(f"Failed to get portfolio summary: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get summary: {str(e)}"
        )


@router.post("/close-all-symbols", response_model=CloseAllResponse)
async def close_all_symbols(
    account_ids: Optional[str] = None,
    symbols: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    전체 포지션 일괄 청산

    **⚠️ 주의**: 이 작업은 되돌릴 수 없습니다!

    **파라미터**:
    - account_ids: 계정 ID 목록 (쉼표 구분, 미지정시 전체)
    - symbols: 심볼 목록 (쉼표 구분, 미지정시 전체)

    **응답**:
    - success: 전체 성공 여부
    - closed_positions: 청산 성공 수
    - failed_positions: 청산 실패 수
    - results: 상세 결과

    **예시**:
    - POST /api/v1/positions/close-all-symbols
    - POST /api/v1/positions/close-all-symbols?symbols=BTC,ETH
    """
    try:
        # 계정 ID 목록 결정
        if account_ids:
            target_account_ids = [aid.strip() for aid in account_ids.split(",")]
        else:
            # DB에서 모든 활성 계정 조회
            all_accounts = db.query(ApiKey).filter(ApiKey.is_active == True).all()
            target_account_ids = [acc.id for acc in all_accounts]

        # 심볼 목록 결정
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
            target_symbols = [SupportedSymbol(s) for s in symbol_list if s in [sym.value for sym in symbol_config.SUPPORTED_SYMBOLS]]
        else:
            target_symbols = symbol_config.SUPPORTED_SYMBOLS

        closed_count = 0
        failed_count = 0
        results = []

        # 각 계정별 포지션 청산
        for account_id in target_account_ids:
            # 계정 정보 조회
            account = db.query(ApiKey).filter(ApiKey.id == account_id).first()
            if not account or not account.is_active:
                continue

            # API 키 복호화
            try:
                decrypted_creds = crypto_service.decrypt_api_credentials({
                    "api_key": account.api_key,
                    "api_secret": account.api_secret,
                    "passphrase": account.passphrase
                })
            except Exception as e:
                logger.error(f"Failed to decrypt credentials for {account_id}: {str(e)}")
                failed_count += 1
                results.append({
                    "account_id": account_id,
                    "success": False,
                    "error": "Decryption failed"
                })
                continue

            exchange_lower = account.exchange.lower()

            try:
                if exchange_lower == "binance":
                    client = BinanceClient(
                        api_key=decrypted_creds["api_key"],
                        api_secret=decrypted_creds["api_secret"],
                        testnet=account.testnet
                    )

                    # 각 심볼별 포지션 청산
                    for symbol in target_symbols:
                        exchange_symbol = symbol_config.get_binance_symbol(symbol)

                        try:
                            result = client.close_position(exchange_symbol)

                            if result["success"]:
                                closed_count += 1
                                results.append({
                                    "account_id": account_id,
                                    "exchange": "binance",
                                    "symbol": symbol.value,
                                    "success": True
                                })
                            else:
                                results.append({
                                    "account_id": account_id,
                                    "exchange": "binance",
                                    "symbol": symbol.value,
                                    "success": False,
                                    "message": result["message"]
                                })
                        except Exception as e:
                            failed_count += 1
                            results.append({
                                "account_id": account_id,
                                "exchange": "binance",
                                "symbol": symbol.value,
                                "success": False,
                                "error": str(e)
                            })

                elif exchange_lower == "okx":
                    client = OKXClient(
                        api_key=decrypted_creds["api_key"],
                        api_secret=decrypted_creds["api_secret"],
                        passphrase=decrypted_creds["passphrase"],
                        testnet=account.testnet
                    )

                    # 각 심볼별 포지션 청산
                    for symbol in target_symbols:
                        exchange_symbol = symbol_config.get_okx_symbol(symbol)

                        try:
                            result = client.close_position(exchange_symbol)

                            if result["success"]:
                                closed_count += 1
                                results.append({
                                    "account_id": account_id,
                                    "exchange": "okx",
                                    "symbol": symbol.value,
                                    "success": True
                                })
                            else:
                                results.append({
                                    "account_id": account_id,
                                    "exchange": "okx",
                                    "symbol": symbol.value,
                                    "success": False,
                                    "message": result["message"]
                                })
                        except Exception as e:
                            failed_count += 1
                            results.append({
                                "account_id": account_id,
                                "exchange": "okx",
                                "symbol": symbol.value,
                                "success": False,
                                "error": str(e)
                            })

            except Exception as e:
                logger.error(f"Failed to close positions for {account_id}: {str(e)}")
                failed_count += 1
                results.append({
                    "account_id": account_id,
                    "success": False,
                    "error": str(e)
                })
                continue

        return CloseAllResponse(
            success=(failed_count == 0),
            closed_positions=closed_count,
            failed_positions=failed_count,
            results=results
        )

    except Exception as e:
        logger.error(f"Failed to close all positions: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to close positions: {str(e)}"
        )
