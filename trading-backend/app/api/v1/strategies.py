"""
Strategy Management API

Endpoints for managing trading strategies and strategy configurations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.database.session import get_db
from app.models.user import User
from app.models.strategy import Strategy, StrategyConfig
from app.workers.auto_trader import auto_trader_manager

router = APIRouter(prefix="/strategies", tags=["strategies"])


# ===== Pydantic Models =====

class StrategyResponse(BaseModel):
    """Strategy response model"""
    id: str
    name: str
    description: str
    category: str
    isPublic: bool
    creatorId: Optional[str]

    # AI weights
    mlWeight: float
    gpt4Weight: float
    claudeWeight: float
    taWeight: float

    # Entry conditions
    minProbability: float
    minConfidence: float
    minAgreement: float

    # Risk management
    defaultLeverage: int
    positionSizePct: float
    slAtrMultiplier: float
    tpAtrMultiplier: float
    maxOpenPositions: int

    # Technical indicators
    atrPeriod: int
    rsiPeriod: int
    macdFast: int
    macdSlow: int
    macdSignal: int

    # Statistics
    usageCount: int
    avgWinRate: Optional[float]
    avgPnl: Optional[float]

    createdAt: datetime
    updatedAt: datetime

    class Config:
        from_attributes = True


class StrategyConfigResponse(BaseModel):
    """Strategy config response model"""
    id: str
    userId: str
    strategyId: str
    name: str
    isActive: bool
    customParams: Optional[dict]

    # Stats
    totalTrades: int
    winRate: Optional[float]
    totalPnl: float
    maxDrawdown: Optional[float]
    sharpeRatio: Optional[float]

    # Auto-trading
    autoTradeEnabled: bool
    selectedSymbols: List[str]

    createdAt: datetime
    updatedAt: datetime
    lastUsedAt: Optional[datetime]

    # Include strategy details
    strategy: StrategyResponse

    class Config:
        from_attributes = True


class CreateStrategyConfigRequest(BaseModel):
    """Create strategy config request"""
    strategyId: str
    name: str
    customParams: Optional[dict] = None
    selectedSymbols: List[str] = Field(default=['BTCUSDT'])


class UpdateStrategyConfigRequest(BaseModel):
    """Update strategy config request"""
    name: Optional[str] = None
    customParams: Optional[dict] = None
    selectedSymbols: Optional[List[str]] = None
    autoTradeEnabled: Optional[bool] = None


class ActivateStrategyRequest(BaseModel):
    """Activate strategy request"""
    isActive: bool


# ===== Helper Functions =====

def get_current_user(db: Session = Depends(get_db)) -> User:
    """Get current authenticated user (placeholder)"""
    # TODO: Implement proper JWT authentication
    # For now, return first user
    user = db.query(User).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found. Please create a user first."
        )
    return user


# ===== Strategy Endpoints =====

@router.get("/", response_model=List[StrategyResponse])
async def list_strategies(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all public strategies

    - **category**: Filter by category (AI_ENSEMBLE, TECHNICAL, FUNDAMENTAL, HYBRID)
    """
    query = db.query(Strategy).filter(Strategy.isPublic == True)

    if category:
        query = query.filter(Strategy.category == category)

    strategies = query.order_by(Strategy.usageCount.desc()).all()

    return strategies


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    db: Session = Depends(get_db)
):
    """Get strategy by ID"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {strategy_id} not found"
        )

    return strategy


# ===== Strategy Config Endpoints =====

@router.get("/configs/my", response_model=List[StrategyConfigResponse])
async def list_my_strategy_configs(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all strategy configurations for current user"""
    configs = db.query(StrategyConfig).filter(
        StrategyConfig.userId == user.id
    ).order_by(StrategyConfig.isActive.desc(), StrategyConfig.updatedAt.desc()).all()

    return configs


@router.post("/configs", response_model=StrategyConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy_config(
    request: CreateStrategyConfigRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new strategy configuration for current user

    - **strategyId**: ID of the strategy template to use
    - **name**: User-friendly name for this configuration
    - **customParams**: Optional custom parameter overrides
    - **selectedSymbols**: Symbols to trade (default: ['BTCUSDT'])
    """
    # Check if strategy exists
    strategy = db.query(Strategy).filter(Strategy.id == request.strategyId).first()
    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy {request.strategyId} not found"
        )

    # Check if user already has config for this strategy
    existing = db.query(StrategyConfig).filter(
        StrategyConfig.userId == user.id,
        StrategyConfig.strategyId == request.strategyId
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Strategy config already exists for {strategy.name}"
        )

    # Create new config
    config = StrategyConfig(
        userId=user.id,
        strategyId=request.strategyId,
        name=request.name,
        customParams=request.customParams,
        selectedSymbols=request.selectedSymbols
    )

    db.add(config)
    db.commit()
    db.refresh(config)

    # Increment strategy usage count
    strategy.usageCount += 1
    db.commit()

    return config


@router.get("/configs/{config_id}", response_model=StrategyConfigResponse)
async def get_strategy_config(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific strategy configuration by ID"""
    config = db.query(StrategyConfig).filter(
        StrategyConfig.id == config_id,
        StrategyConfig.userId == user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy config {config_id} not found"
        )

    return config


@router.put("/configs/{config_id}", response_model=StrategyConfigResponse)
async def update_strategy_config(
    config_id: str,
    request: UpdateStrategyConfigRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing strategy configuration

    - **name**: Update user-friendly name
    - **customParams**: Update custom parameter overrides
    - **selectedSymbols**: Update trading symbols
    - **autoTradeEnabled**: Enable/disable auto-trading
    """
    # Get config
    config = db.query(StrategyConfig).filter(
        StrategyConfig.id == config_id,
        StrategyConfig.userId == user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy config {config_id} not found"
        )

    # Update fields
    if request.name is not None:
        config.name = request.name

    if request.customParams is not None:
        config.customParams = request.customParams

    if request.selectedSymbols is not None:
        config.selectedSymbols = request.selectedSymbols

    if request.autoTradeEnabled is not None:
        config.autoTradeEnabled = request.autoTradeEnabled

    config.updatedAt = datetime.utcnow()

    db.commit()
    db.refresh(config)

    return config


@router.post("/configs/{config_id}/activate", response_model=StrategyConfigResponse)
async def activate_strategy_config(
    config_id: str,
    request: ActivateStrategyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate a strategy configuration

    Only one strategy can be active at a time per user.
    If activating, all other configs will be deactivated.

    - **isActive**: True to activate, False to deactivate
    """
    # Get config
    config = db.query(StrategyConfig).filter(
        StrategyConfig.id == config_id,
        StrategyConfig.userId == user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy config {config_id} not found"
        )

    if request.isActive:
        # Deactivate all other configs for this user
        db.query(StrategyConfig).filter(
            StrategyConfig.userId == user.id,
            StrategyConfig.id != config_id
        ).update({'isActive': False})

        # Activate this config
        config.isActive = True
        config.lastUsedAt = datetime.utcnow()
    else:
        # Deactivate this config
        config.isActive = False

    db.commit()
    db.refresh(config)

    return config


@router.delete("/configs/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy_config(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a strategy configuration"""
    # Get config
    config = db.query(StrategyConfig).filter(
        StrategyConfig.id == config_id,
        StrategyConfig.userId == user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy config {config_id} not found"
        )

    # Check if auto-trading is enabled
    if config.autoTradeEnabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete strategy config with auto-trading enabled. Disable auto-trading first."
        )

    db.delete(config)
    db.commit()

    return None


# ===== Auto-Trading Control Endpoints =====

@router.post("/auto-trade/start")
async def start_auto_trading(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start auto-trading for current user

    Requires:
    - Active strategy configuration with autoTradeEnabled=True
    - Active Binance API key
    """
    try:
        await auto_trader_manager.start_trader(user_id=user.id, db=db)

        return {
            'success': True,
            'message': f'Auto-trading started for user {user.id}'
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error starting auto-trading: {str(e)}'
        )


@router.post("/auto-trade/stop")
async def stop_auto_trading(
    user: User = Depends(get_current_user)
):
    """Stop auto-trading for current user"""
    try:
        await auto_trader_manager.stop_trader(user_id=user.id)

        return {
            'success': True,
            'message': f'Auto-trading stopped for user {user.id}'
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Error stopping auto-trading: {str(e)}'
        )


@router.get("/auto-trade/status")
async def get_auto_trading_status(
    user: User = Depends(get_current_user)
):
    """Get auto-trading status for current user"""
    status = auto_trader_manager.get_trader_status(user_id=user.id)
    return status


@router.get("/auto-trade/active")
async def list_active_traders():
    """List all active auto-traders (admin endpoint)"""
    traders = auto_trader_manager.list_active_traders()
    return {
        'count': len(traders),
        'traders': traders
    }


# ===== Backtesting Endpoints =====

@router.get("/configs/{config_id}/backtest")
async def get_backtest_data(
    config_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get backtesting data for a strategy configuration

    Returns simulated historical performance data including:
    - Equity curve
    - Daily P&L
    - Drawdown analysis
    - Trade frequency
    - Performance metrics
    """
    # Get config
    config = db.query(StrategyConfig).filter(
        StrategyConfig.id == config_id,
        StrategyConfig.userId == user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy config {config_id} not found"
        )

    # TODO: Implement actual backtesting engine
    # For now, return mock data for demonstration

    import random
    from datetime import datetime, timedelta

    # Generate 30 days of mock backtesting data
    start_date = datetime.now() - timedelta(days=30)
    equity = 10000.0
    max_equity = equity

    backtest_data = []
    for i in range(30):
        date = start_date + timedelta(days=i)

        # Simulate daily P&L (random walk with slight positive bias)
        daily_pnl = random.uniform(-200, 250)
        equity += daily_pnl

        # Track max equity for drawdown calculation
        if equity > max_equity:
            max_equity = equity

        # Calculate drawdown
        drawdown = (equity - max_equity) / max_equity if max_equity > 0 else 0

        # Simulate trades
        trades = random.randint(0, 8)

        backtest_data.append({
            'timestamp': date.strftime('%Y-%m-%d'),
            'cumulativePnl': equity - 10000,
            'dailyPnl': daily_pnl,
            'drawdown': drawdown,
            'equity': equity,
            'trades': trades
        })

    # Calculate metrics
    total_pnl = equity - 10000
    wins = sum(1 for d in backtest_data if d['dailyPnl'] > 0)
    losses = sum(1 for d in backtest_data if d['dailyPnl'] < 0)
    total_trades = wins + losses

    avg_win = sum(d['dailyPnl'] for d in backtest_data if d['dailyPnl'] > 0) / wins if wins > 0 else 0
    avg_loss = sum(d['dailyPnl'] for d in backtest_data if d['dailyPnl'] < 0) / losses if losses > 0 else 0

    metrics = {
        'totalTrades': total_trades,
        'winRate': wins / total_trades if total_trades > 0 else 0,
        'totalPnl': total_pnl,
        'maxDrawdown': min(d['drawdown'] for d in backtest_data),
        'sharpeRatio': random.uniform(0.5, 2.5),  # Mock Sharpe ratio
        'avgWin': avg_win,
        'avgLoss': abs(avg_loss),
        'profitFactor': abs(avg_win / avg_loss) if avg_loss != 0 else 0
    }

    return {
        'data': backtest_data,
        'metrics': metrics
    }


# ===== Performance Analytics Endpoints =====

@router.get("/configs/{config_id}/performance")
async def get_strategy_performance(
    config_id: str,
    range: str = '30d',
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive performance analytics for a strategy configuration

    Returns detailed performance data including:
    - Equity curve and drawdown
    - Daily PnL distribution
    - Win/Loss distribution
    - Trading hours analysis
    - Symbol-specific performance
    - Comprehensive metrics
    """
    # Get config
    config = db.query(StrategyConfig).filter(
        StrategyConfig.id == config_id,
        StrategyConfig.userId == user.id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Strategy config {config_id} not found"
        )

    # TODO: Implement actual performance analytics from trade history
    # For now, return mock data for demonstration

    import random
    from datetime import datetime, timedelta

    # Determine date range
    days = {'7d': 7, '30d': 30, '90d': 90, 'all': 180}.get(range, 30)
    start_date = datetime.now() - timedelta(days=days)

    # Generate equity curve
    equity = 10000.0
    max_equity = equity
    equity_curve = []

    for i in range(days):
        date = start_date + timedelta(days=i)
        daily_pnl = random.uniform(-150, 200)
        equity += daily_pnl

        if equity > max_equity:
            max_equity = equity

        drawdown = (equity - max_equity) / max_equity if max_equity > 0 else 0

        equity_curve.append({
            'timestamp': date.strftime('%Y-%m-%d'),
            'equity': round(equity, 2),
            'drawdown': round(drawdown, 4)
        })

    # Generate daily PnL
    daily_pnl = []
    for i in range(days):
        date = (start_date + timedelta(days=i)).strftime('%Y-%m-%d')
        pnl = random.uniform(-150, 200)
        trades = random.randint(0, 5)

        daily_pnl.append({
            'date': date,
            'pnl': round(pnl, 2),
            'trades': trades
        })

    # Generate win/loss distribution
    win_loss_distribution = [
        {'range': '-$200~-$100', 'count': random.randint(2, 8), 'percentage': 0},
        {'range': '-$100~-$50', 'count': random.randint(5, 15), 'percentage': 0},
        {'range': '-$50~$0', 'count': random.randint(10, 20), 'percentage': 0},
        {'range': '$0~$50', 'count': random.randint(15, 30), 'percentage': 0},
        {'range': '$50~$100', 'count': random.randint(10, 25), 'percentage': 0},
        {'range': '$100~$200', 'count': random.randint(5, 15), 'percentage': 0},
        {'range': '$200+', 'count': random.randint(2, 8), 'percentage': 0}
    ]

    # Calculate percentages
    total_count = sum(d['count'] for d in win_loss_distribution)
    for d in win_loss_distribution:
        d['percentage'] = round(d['count'] / total_count * 100, 1) if total_count > 0 else 0

    # Generate trading hours analysis
    trading_hours = []
    for hour in range(24):
        trades = random.randint(0, 15)
        avg_pnl = random.uniform(-10, 15)

        trading_hours.append({
            'hour': hour,
            'trades': trades,
            'avg_pnl': round(avg_pnl, 2)
        })

    # Generate symbol performance
    symbols = config.selectedSymbols if config.selectedSymbols else ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']
    symbol_performance = []

    for symbol in symbols:
        trades = random.randint(20, 100)
        win_rate = random.uniform(0.45, 0.75)
        total_pnl = random.uniform(-500, 1500)

        symbol_performance.append({
            'symbol': symbol.replace('USDT', '/USDT'),
            'trades': trades,
            'win_rate': round(win_rate, 3),
            'total_pnl': round(total_pnl, 2),
            'avg_pnl': round(total_pnl / trades, 2)
        })

    # Calculate comprehensive metrics
    total_trades = sum(s['trades'] for s in symbol_performance)
    total_pnl = sum(s['total_pnl'] for s in symbol_performance)
    avg_win_rate = sum(s['win_rate'] for s in symbol_performance) / len(symbol_performance)

    wins = int(total_trades * avg_win_rate)
    losses = total_trades - wins

    avg_win = abs(total_pnl) / wins if wins > 0 else 0
    avg_loss = abs(total_pnl) * 0.6 / losses if losses > 0 else 0

    metrics = {
        'total_trades': total_trades,
        'win_rate': round(avg_win_rate, 3),
        'total_pnl': round(total_pnl, 2),
        'avg_win': round(avg_win, 2),
        'avg_loss': round(avg_loss, 2),
        'profit_factor': round(avg_win / avg_loss, 2) if avg_loss > 0 else 0,
        'sharpe_ratio': round(random.uniform(0.8, 2.2), 2),
        'max_drawdown': round(min(e['drawdown'] for e in equity_curve), 4),
        'avg_holding_time': random.randint(180, 1200),  # minutes
        'best_trade': round(random.uniform(200, 500), 2),
        'worst_trade': round(random.uniform(-200, -50), 2),
        'consecutive_wins': random.randint(3, 12),
        'consecutive_losses': random.randint(2, 8)
    }

    return {
        'equity_curve': equity_curve,
        'daily_pnl': daily_pnl,
        'win_loss_distribution': win_loss_distribution,
        'trading_hours': trading_hours,
        'symbol_performance': symbol_performance,
        'metrics': metrics
    }
