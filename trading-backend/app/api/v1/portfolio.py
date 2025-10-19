"""
Portfolio Management API

고급 포트폴리오 관리 기능:
- 상관관계 분석
- VaR, MDD, Sharpe Ratio
- 리밸런싱 계산
- 포지션 집중도
- 청산 가격
"""

import logging
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.api_key import ApiKey
from app.core.crypto import crypto_service
from app.services.binance_client import BinanceClient
from app.services.okx_client import OKXClient
from app.services.portfolio_analyzer import portfolio_analyzer

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class CorrelationResponse(BaseModel):
    """상관관계 매트릭스 응답"""
    correlation_matrix: Dict[str, Dict[str, float]]
    symbols: List[str]
    data_points: int


class RiskMetricsResponse(BaseModel):
    """리스크 지표 응답"""
    var: Dict[str, Any]
    mdd: Optional[Dict[str, float]] = None
    sharpe_ratio: Optional[float] = None
    concentration: Dict[str, Any]
    total_exposure: float
    portfolio_value: float


class RebalancingRequest(BaseModel):
    """리밸런싱 요청"""
    target_allocation: Dict[str, float] = Field(..., description="목표 배분 (%) {symbol: percentage}")
    account_ids: Optional[List[str]] = Field(None, description="계정 ID 리스트")
    min_order_value: float = Field(10.0, description="최소 주문 금액 (USDT)")


class RebalancingResponse(BaseModel):
    """리밸런싱 응답"""
    orders: List[Dict[str, Any]]
    current_allocation: Dict[str, float]
    target_allocation: Dict[str, float]
    portfolio_value: float
    total_orders: int


class LiquidationPricesResponse(BaseModel):
    """청산 가격 응답"""
    liquidation_prices: List[Dict[str, Any]]
    total_positions: int
    critical_positions: List[Dict[str, Any]]  # 청산가까지 10% 이내


# ============================================================================
# Helper Functions
# ============================================================================

async def get_historical_prices(
    exchange: str,
    symbols: List[str],
    days: int = 30
) -> Dict[str, List[float]]:
    """
    과거 가격 데이터 조회 (상관관계 분석용)

    실제 구현에서는 거래소 API에서 kline 데이터를 가져와야 하지만,
    여기서는 간단한 예시 데이터를 생성합니다.
    """
    import random
    import numpy as np

    # 실제 환경에서는 거래소 API의 get_klines() 메서드를 사용해야 합니다
    # 예: client.get_klines(symbol, interval="1d", limit=days)

    price_data = {}

    for symbol in symbols:
        # 예시: 랜덤 워크 데이터 생성
        base_price = {"BTC": 50000, "ETH": 3000, "SOL": 100, "ADA": 0.5}.get(symbol, 100)
        returns = np.random.normal(0.001, 0.02, days)  # 평균 0.1%, 표준편차 2%
        prices = [base_price]

        for ret in returns:
            prices.append(prices[-1] * (1 + ret))

        price_data[symbol] = prices[1:]  # 첫 번째 제외

    return price_data


async def get_all_positions(
    account_ids: Optional[List[str]],
    db: Session
) -> List[Dict[str, Any]]:
    """모든 계정의 포지션 조회"""
    if account_ids:
        target_account_ids = account_ids
    else:
        all_accounts = db.query(ApiKey).filter(ApiKey.is_active == True).all()
        target_account_ids = [acc.id for acc in all_accounts]

    all_positions = []

    for account_id in target_account_ids:
        account = db.query(ApiKey).filter(ApiKey.id == account_id).first()
        if not account or not account.is_active:
            continue

        try:
            # API 키 복호화
            decrypted_creds = crypto_service.decrypt_api_credentials({
                "api_key": account.api_key,
                "api_secret": account.api_secret,
                "passphrase": account.passphrase
            })

            # 거래소별 클라이언트 생성
            if account.exchange.lower() == "binance":
                client = BinanceClient(
                    api_key=decrypted_creds["api_key"],
                    api_secret=decrypted_creds["api_secret"],
                    testnet=account.testnet
                )
            elif account.exchange.lower() == "okx":
                client = OKXClient(
                    api_key=decrypted_creds["api_key"],
                    api_secret=decrypted_creds["api_secret"],
                    passphrase=decrypted_creds["passphrase"],
                    testnet=account.testnet
                )
            else:
                continue

            # 포지션 조회
            positions = client.get_positions()

            for pos in positions:
                pos["account_id"] = account_id
                pos["exchange"] = account.exchange.lower()
                all_positions.append(pos)

        except Exception as e:
            logger.error(f"Failed to get positions for account {account_id}: {str(e)}")
            continue

    return all_positions


# ============================================================================
# API Endpoints
# ============================================================================

@router.get("/correlation", response_model=CorrelationResponse)
async def get_correlation_matrix(
    exchange: str = Query("binance", description="거래소 (binance/okx)"),
    symbols: Optional[str] = Query(None, description="심볼 목록 (쉼표 구분)"),
    days: int = Query(30, description="분석 기간 (일)", ge=7, le=365)
):
    """
    상관관계 매트릭스 조회

    4개 코인(BTC, ETH, SOL, ADA) 간 가격 상관관계를 분석합니다.
    """
    try:
        # 심볼 목록 결정
        if symbols:
            symbol_list = [s.strip().upper() for s in symbols.split(",")]
        else:
            symbol_list = ["BTC", "ETH", "SOL", "ADA"]

        # 과거 가격 데이터 조회
        price_data = await get_historical_prices(exchange, symbol_list, days)

        # 상관관계 계산
        correlation_matrix = portfolio_analyzer.calculate_correlation_matrix(price_data)

        return CorrelationResponse(
            correlation_matrix=correlation_matrix,
            symbols=symbol_list,
            data_points=len(price_data[symbol_list[0]])
        )

    except Exception as e:
        logger.error(f"Failed to calculate correlation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/risk-metrics", response_model=RiskMetricsResponse)
async def get_risk_metrics(
    account_ids: Optional[str] = Query(None, description="계정 ID 목록 (쉼표 구분)"),
    confidence_level: float = Query(0.95, description="VaR 신뢰 수준", ge=0.9, le=0.99),
    db: Session = Depends(get_db)
):
    """
    포트폴리오 리스크 지표 조회

    VaR, MDD, Sharpe Ratio, 포지션 집중도 등을 제공합니다.
    """
    try:
        # 계정 ID 파싱
        account_id_list = None
        if account_ids:
            account_id_list = [aid.strip() for aid in account_ids.split(",")]

        # 모든 포지션 조회
        positions = await get_all_positions(account_id_list, db)

        if not positions:
            raise HTTPException(status_code=404, detail="No positions found")

        # VaR 계산
        var_result = portfolio_analyzer.calculate_portfolio_var(
            positions,
            confidence_level=confidence_level
        )

        # 포지션 집중도
        concentration = portfolio_analyzer.calculate_position_concentration(positions)

        # 총 노출 금액
        total_exposure = sum(
            abs(pos.get("size", 0)) * pos.get("current_price", 0) * pos.get("leverage", 1)
            for pos in positions
        )

        # MDD 계산 (실제로는 equity curve 필요, 여기서는 생략)
        mdd_result = None

        # Sharpe Ratio (실제로는 과거 수익률 필요, 여기서는 생략)
        sharpe_ratio = None

        return RiskMetricsResponse(
            var=var_result,
            mdd=mdd_result,
            sharpe_ratio=sharpe_ratio,
            concentration=concentration,
            total_exposure=round(total_exposure, 2),
            portfolio_value=var_result["portfolio_value"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate risk metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rebalancing", response_model=RebalancingResponse)
async def calculate_rebalancing(
    request: RebalancingRequest,
    db: Session = Depends(get_db)
):
    """
    리밸런싱 주문 계산

    현재 포트폴리오를 목표 배분 비율로 리밸런싱하는데 필요한 주문을 계산합니다.
    """
    try:
        # 목표 배분 검증
        total_pct = sum(request.target_allocation.values())
        if abs(total_pct - 100) > 0.1:
            raise HTTPException(
                status_code=400,
                detail=f"Target allocation must sum to 100%, got {total_pct}%"
            )

        # 모든 포지션 조회
        positions = await get_all_positions(request.account_ids, db)

        if not positions:
            raise HTTPException(status_code=404, detail="No positions found")

        # 포트폴리오 총 가치
        portfolio_value = sum(
            abs(pos.get("size", 0)) * pos.get("current_price", 0)
            for pos in positions
        )

        # 현재 배분 계산
        current_allocation = {}
        symbol_values = {}

        for pos in positions:
            symbol = pos.get("symbol", "").replace("USDT", "")
            value = abs(pos.get("size", 0)) * pos.get("current_price", 0)

            if symbol not in symbol_values:
                symbol_values[symbol] = 0
            symbol_values[symbol] += value

        for symbol, value in symbol_values.items():
            current_allocation[symbol] = (value / portfolio_value) * 100 if portfolio_value > 0 else 0

        # 현재 가격 수집
        current_prices = {}
        for pos in positions:
            symbol = pos.get("symbol", "").replace("USDT", "")
            if symbol not in current_prices:
                current_prices[symbol] = pos.get("current_price", 0)

        # 리밸런싱 주문 계산
        orders = portfolio_analyzer.calculate_rebalancing_orders(
            current_allocation=current_allocation,
            target_allocation=request.target_allocation,
            portfolio_value=portfolio_value,
            current_prices=current_prices,
            min_order_value=request.min_order_value
        )

        return RebalancingResponse(
            orders=orders,
            current_allocation=current_allocation,
            target_allocation=request.target_allocation,
            portfolio_value=round(portfolio_value, 2),
            total_orders=len(orders)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate rebalancing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/liquidation", response_model=LiquidationPricesResponse)
async def get_liquidation_prices(
    account_ids: Optional[str] = Query(None, description="계정 ID 목록 (쉼표 구분)"),
    maintenance_margin_rate: float = Query(0.004, description="유지 증거금 비율", ge=0.001, le=0.01),
    db: Session = Depends(get_db)
):
    """
    청산 가격 조회

    모든 포지션의 청산 가격과 현재 가격과의 거리를 계산합니다.
    """
    try:
        # 계정 ID 파싱
        account_id_list = None
        if account_ids:
            account_id_list = [aid.strip() for aid in account_ids.split(",")]

        # 모든 포지션 조회
        positions = await get_all_positions(account_id_list, db)

        if not positions:
            raise HTTPException(status_code=404, detail="No positions found")

        # 청산 가격 계산
        liquidation_prices = portfolio_analyzer.calculate_liquidation_prices(
            positions,
            maintenance_margin_rate=maintenance_margin_rate
        )

        # Critical positions (청산가까지 10% 이내)
        critical_positions = [
            liq for liq in liquidation_prices
            if liq["distance_percentage"] <= 10.0
        ]

        return LiquidationPricesResponse(
            liquidation_prices=liquidation_prices,
            total_positions=len(liquidation_prices),
            critical_positions=critical_positions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get liquidation prices: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concentration")
async def get_position_concentration(
    account_ids: Optional[str] = Query(None, description="계정 ID 목록 (쉼표 구분)"),
    db: Session = Depends(get_db)
):
    """
    포지션 집중도 분석

    포트폴리오의 다각화 수준을 분석합니다.
    """
    try:
        # 계정 ID 파싱
        account_id_list = None
        if account_ids:
            account_id_list = [aid.strip() for aid in account_ids.split(",")]

        # 모든 포지션 조회
        positions = await get_all_positions(account_id_list, db)

        if not positions:
            raise HTTPException(status_code=404, detail="No positions found")

        # 집중도 계산
        concentration = portfolio_analyzer.calculate_position_concentration(positions)

        return concentration

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to calculate concentration: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
