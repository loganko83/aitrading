from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.binance import BinanceFuturesClient
from app.ai.ensemble import TripleAIEnsemble
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request model for market analysis"""
    symbol: str = "BTCUSDT"
    interval: str = "1h"
    limit: int = 500


class TradeRequest(BaseModel):
    """Request model for executing trades"""
    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: float
    leverage: Optional[int] = 3


@router.post("/analyze")
async def analyze_market(request: AnalyzeRequest):
    """
    Analyze market using Triple AI Ensemble

    Returns trading signal with probability, confidence, and agreement metrics
    """
    try:
        # Initialize clients
        binance = BinanceFuturesClient()
        ensemble = TripleAIEnsemble()

        # Fetch market data
        market_data = await binance.get_market_data(
            symbol=request.symbol,
            interval=request.interval,
            limit=request.limit
        )

        current_price = await binance.get_current_price(request.symbol)

        # Analyze with AI Ensemble
        decision = await ensemble.analyze(
            symbol=request.symbol,
            market_data=market_data,
            current_price=current_price
        )

        return {
            "success": True,
            "symbol": request.symbol,
            "current_price": current_price,
            "decision": {
                "should_enter": decision.should_enter,
                "direction": decision.direction,
                "probability_up": decision.probability_up,
                "confidence": decision.confidence,
                "agreement": decision.agreement,
                "entry_price": decision.entry_price,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "reasoning": decision.reasoning
            },
            "ai_results": {
                "ml": {
                    "direction": decision.ml_result.direction,
                    "probability": decision.ml_result.probability,
                    "confidence": decision.ml_result.confidence,
                    "reasoning": decision.ml_result.reasoning
                },
                "gpt4": {
                    "direction": decision.gpt4_result.direction,
                    "probability": decision.gpt4_result.probability,
                    "confidence": decision.gpt4_result.confidence,
                    "reasoning": decision.gpt4_result.reasoning
                },
                "llama": {
                    "direction": decision.llama_result.direction,
                    "probability": decision.llama_result.probability,
                    "confidence": decision.llama_result.confidence,
                    "reasoning": decision.llama_result.reasoning
                },
                "ta": {
                    "direction": decision.ta_result.direction,
                    "probability": decision.ta_result.probability,
                    "confidence": decision.ta_result.confidence,
                    "reasoning": decision.ta_result.reasoning
                }
            }
        }

    except Exception as e:
        logger.error(f"Error analyzing market: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positions")
async def get_positions():
    """Get all open positions"""
    try:
        binance = BinanceFuturesClient()
        positions = await binance.get_open_positions()

        return {
            "success": True,
            "positions": positions
        }

    except Exception as e:
        logger.error(f"Error fetching positions: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/balance")
async def get_balance():
    """Get account balance"""
    try:
        binance = BinanceFuturesClient()
        balance = await binance.get_account_balance()

        return {
            "success": True,
            "balance": balance
        }

    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trade")
async def execute_trade(request: TradeRequest):
    """
    Execute a market order

    Requires: symbol, side (BUY/SELL), quantity, leverage
    """
    try:
        binance = BinanceFuturesClient()

        # Set leverage
        await binance.set_leverage(
            symbol=request.symbol,
            leverage=request.leverage
        )

        # Place market order
        order = await binance.place_market_order(
            symbol=request.symbol,
            side=request.side,
            quantity=request.quantity
        )

        return {
            "success": True,
            "order": order
        }

    except Exception as e:
        logger.error(f"Error executing trade: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/close-position")
async def close_position(symbol: str, quantity: Optional[float] = None):
    """
    Close an open position

    Args:
        symbol: Trading pair (e.g., BTCUSDT)
        quantity: Amount to close (None = close all)
    """
    try:
        binance = BinanceFuturesClient()

        order = await binance.close_position(
            symbol=symbol,
            quantity=quantity
        )

        return {
            "success": True,
            "order": order
        }

    except Exception as e:
        logger.error(f"Error closing position: {e}")
        raise HTTPException(status_code=500, detail=str(e))
