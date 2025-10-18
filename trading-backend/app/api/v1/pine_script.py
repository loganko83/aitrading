"""
Pine Script Management API

Features:
- 전략 라이브러리 조회
- Pine Script 분석
- AI 기반 전략 생성
- 전략 커스터마이징
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import logging

from app.services.pine_script_analyzer import pine_analyzer, StrategyInfo, StrategyMetrics
from app.services.strategy_optimizer import strategy_optimizer, StrategyTemplate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pine-script", tags=["pine_script"])


# ==================== Request/Response Models ====================

class StrategyListRequest(BaseModel):
    """전략 목록 조회 요청"""
    category: Optional[str] = Field(None, description="카테고리 필터 (Trend Following, Mean Reversion, etc.)")
    difficulty: Optional[str] = Field(None, description="난이도 필터 (Beginner, Intermediate, Advanced)")
    min_popularity: int = Field(0, description="최소 인기도 (0-100)", ge=0, le=100)


class StrategyTemplateResponse(BaseModel):
    """전략 템플릿 응답"""
    id: str
    name: str
    description: str
    author: str
    category: str
    difficulty: str
    popularity_score: int
    indicators: List[str]
    default_parameters: Dict[str, Any]
    backtest_results: Optional[Dict[str, float]] = None


class CustomizeStrategyRequest(BaseModel):
    """전략 커스터마이징 요청"""
    strategy_id: str = Field(..., description="전략 템플릿 ID (예: ema_crossover)")
    account_id: str = Field(..., description="계정 ID")
    webhook_secret: str = Field(..., description="Webhook Secret", min_length=32)
    custom_parameters: Optional[Dict[str, Any]] = Field(None, description="커스터마이징 파라미터")
    symbol: str = Field("BTCUSDT", description="거래 심볼")


class CustomizeStrategyResponse(BaseModel):
    """커스터마이징된 전략 응답"""
    strategy_id: str
    strategy_name: str
    pine_script_code: str
    parameters: Dict[str, Any]
    instructions: List[str]


class AnalyzePineScriptRequest(BaseModel):
    """Pine Script 분석 요청"""
    code: str = Field(..., description="분석할 Pine Script 코드", min_length=10)
    include_ai_analysis: bool = Field(True, description="AI 분석 포함 여부")


class StrategyAnalysisResponse(BaseModel):
    """전략 분석 응답"""
    strategy_info: Dict[str, Any]
    ai_analysis: Optional[Dict[str, Any]] = None
    recommendations: List[str]
    quality_score: Optional[float] = None


class OptimizeParametersRequest(BaseModel):
    """파라미터 최적화 요청"""
    strategy_id: str = Field(..., description="전략 템플릿 ID")
    market_conditions: Dict[str, Any] = Field(
        ...,
        description="시장 상황 (volatility: Low/Medium/High, trend: Bullish/Bearish/Neutral)"
    )


class GenerateStrategyRequest(BaseModel):
    """AI 전략 생성 요청"""
    description: str = Field(..., description="원하는 전략 설명 (한글 가능)", min_length=10)
    account_id: str
    webhook_secret: str
    risk_level: str = Field("Medium", description="리스크 레벨 (Low/Medium/High)")
    preferred_indicators: Optional[List[str]] = Field(None, description="선호하는 인디케이터")


# ==================== API Endpoints ====================

@router.get("/strategies", response_model=List[StrategyTemplateResponse])
async def list_strategies(
    category: Optional[str] = None,
    difficulty: Optional[str] = None,
    min_popularity: int = 0
):
    """
    전략 라이브러리 조회

    **카테고리**:
    - Trend Following: 트렌드 추종 전략
    - Mean Reversion: 평균 회귀 전략
    - Breakout: 돌파 전략

    **난이도**:
    - Beginner: 초보자용
    - Intermediate: 중급자용
    - Advanced: 고급자용

    **인기도**: 0-100 (커뮤니티 평가 기준)
    """
    try:
        strategies = strategy_optimizer.list_strategies(
            category=category,
            difficulty=difficulty,
            min_popularity=min_popularity
        )

        return [
            StrategyTemplateResponse(
                id=s.id,
                name=s.name,
                description=s.description,
                author=s.author,
                category=s.category,
                difficulty=s.difficulty,
                popularity_score=s.popularity_score,
                indicators=s.indicators,
                default_parameters=s.default_parameters,
                backtest_results=s.backtest_results
            )
            for s in strategies
        ]

    except Exception as e:
        logger.error(f"Failed to list strategies: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies/{strategy_id}", response_model=StrategyTemplateResponse)
async def get_strategy(strategy_id: str):
    """
    특정 전략 조회

    **사용 가능한 전략**:
    - `ema_crossover`: EMA 크로스오버 (초보자 추천)
    - `rsi_reversal`: RSI 평균 회귀
    - `macd_rsi_combo`: MACD + RSI 복합 전략
    - `bb_breakout`: 볼린저 밴드 돌파
    - `supertrend`: SuperTrend (고급)
    """
    template = strategy_optimizer.get_strategy_by_id(strategy_id)

    if not template:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy not found: {strategy_id}. Available strategies: {list(strategy_optimizer.strategy_library.keys())}"
        )

    return StrategyTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        author=template.author,
        category=template.category,
        difficulty=template.difficulty,
        popularity_score=template.popularity_score,
        indicators=template.indicators,
        default_parameters=template.default_parameters,
        backtest_results=template.backtest_results
    )


@router.post("/customize", response_model=CustomizeStrategyResponse)
async def customize_strategy(request: CustomizeStrategyRequest):
    """
    전략 커스터마이징 (Webhook 자동 통합)

    **사용 방법**:
    1. 원하는 전략 ID 선택 (예: `ema_crossover`)
    2. 계정 ID와 Webhook Secret 입력
    3. 파라미터 커스터마이징 (선택)
    4. 생성된 Pine Script를 TradingView에 붙여넣기

    **예시**:
    ```json
    {
      "strategy_id": "ema_crossover",
      "account_id": "my_binance_account",
      "webhook_secret": "your_webhook_secret",
      "custom_parameters": {
        "fast_length": 12,
        "slow_length": 26,
        "leverage": 5
      }
    }
    ```
    """
    try:
        # 전략 템플릿 조회
        template = strategy_optimizer.get_strategy_by_id(request.strategy_id)

        if not template:
            raise HTTPException(
                status_code=404,
                detail=f"Strategy not found: {request.strategy_id}"
            )

        # 전략 커스터마이징
        customized_code = strategy_optimizer.customize_strategy(
            template=template,
            account_id=request.account_id,
            webhook_secret=request.webhook_secret,
            parameters=request.custom_parameters
        )

        # 심볼 교체
        customized_code = customized_code.replace("BTCUSDT", request.symbol)

        # 사용 파라미터 결정
        final_params = {**template.default_parameters}
        if request.custom_parameters:
            final_params.update(request.custom_parameters)

        # 사용 방법 안내
        instructions = [
            "1. TradingView Pine Editor 열기",
            "2. 아래 코드를 복사하여 붙여넣기",
            "3. 'Add to chart' 클릭",
            "4. 차트 우측 상단 '알림' 아이콘 클릭 → '생성'",
            "5. 조건: 현재 전략명 선택, alert() function calls only",
            f"6. Webhook URL: http://YOUR_SERVER/api/v1/webhook/tradingview",
            "7. '생성' 클릭",
            "8. 백테스팅 결과 확인 후 실전 적용"
        ]

        return CustomizeStrategyResponse(
            strategy_id=request.strategy_id,
            strategy_name=template.name,
            pine_script_code=customized_code,
            parameters=final_params,
            instructions=instructions
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to customize strategy: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze", response_model=StrategyAnalysisResponse)
async def analyze_pine_script(request: AnalyzePineScriptRequest):
    """
    Pine Script 분석 (AI 기반)

    **분석 내용**:
    - 전략 정보 추출 (이름, 버전, 인디케이터)
    - 진입/청산 조건 파악
    - 리스크 관리 설정 확인
    - AI 기반 코드 품질 평가 (GPT-4 + Claude)
    - 개선 추천사항

    **사용 예시**:
    ```json
    {
      "code": "//@version=5\\nstrategy(\\"My Strategy\\")\\n...",
      "include_ai_analysis": true
    }
    ```
    """
    try:
        # 1. Pine Script 파싱
        strategy_info = pine_analyzer.parse_pine_script(request.code)

        # 2. AI 분석 (선택사항)
        ai_analysis = None
        quality_score = None

        if request.include_ai_analysis:
            ai_analysis = await pine_analyzer.analyze_with_ai(request.code, strategy_info)
            quality_score = ai_analysis.get("consensus", {}).get("average_quality_score")

        # 3. 추천사항 생성
        recommendations = []

        if not strategy_info.has_webhook:
            recommendations.append("⚠️ Webhook 알림이 없습니다. 자동매매를 위해 alert() 함수를 추가하세요.")

        if not strategy_info.risk_management.get("stop_loss"):
            recommendations.append("⚠️ 손절매 설정이 없습니다. strategy.exit()로 손절 설정을 추가하세요.")

        if len(strategy_info.indicators) == 1:
            recommendations.append("💡 단일 인디케이터 사용 중입니다. 필터 추가로 신뢰도를 높일 수 있습니다.")

        if quality_score and quality_score < 70:
            recommendations.append("⚠️ 코드 품질이 낮습니다. AI 분석 결과를 참고하여 개선하세요.")

        # 4. 응답 생성
        return StrategyAnalysisResponse(
            strategy_info={
                "name": strategy_info.name,
                "version": strategy_info.version,
                "description": strategy_info.description,
                "indicators": strategy_info.indicators,
                "parameters": strategy_info.parameters,
                "entry_conditions": strategy_info.entry_conditions,
                "exit_conditions": strategy_info.exit_conditions,
                "risk_management": strategy_info.risk_management,
                "has_webhook": strategy_info.has_webhook
            },
            ai_analysis=ai_analysis,
            recommendations=recommendations,
            quality_score=quality_score
        )

    except Exception as e:
        logger.error(f"Failed to analyze Pine Script: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-parameters")
async def optimize_parameters(request: OptimizeParametersRequest):
    """
    AI 기반 파라미터 최적화

    현재 시장 상황에 맞게 전략 파라미터를 AI가 최적화합니다.

    **시장 상황 입력 예시**:
    ```json
    {
      "strategy_id": "ema_crossover",
      "market_conditions": {
        "volatility": "High",
        "trend": "Bullish",
        "volume": "Above Average"
      }
    }
    ```
    """
    try:
        template = strategy_optimizer.get_strategy_by_id(request.strategy_id)

        if not template:
            raise HTTPException(404, f"Strategy not found: {request.strategy_id}")

        optimized_params = await strategy_optimizer.optimize_parameters(
            template=template,
            market_conditions=request.market_conditions
        )

        return {
            "strategy_id": request.strategy_id,
            "original_parameters": template.default_parameters,
            "optimized_parameters": optimized_params,
            "market_conditions": request.market_conditions,
            "recommendation": "백테스팅으로 최적화된 파라미터의 성과를 검증한 후 적용하세요."
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parameter optimization failed: {str(e)}", exc_info=True)
        raise HTTPException(500, str(e))


@router.post("/generate")
async def generate_strategy(request: GenerateStrategyRequest):
    """
    AI 기반 전략 생성 (실험적 기능)

    자연어로 원하는 전략을 설명하면 AI가 Pine Script를 자동 생성합니다.

    **예시**:
    ```json
    {
      "description": "RSI가 30 이하일 때 롱 진입, 70 이상일 때 청산하는 전략을 만들어주세요",
      "account_id": "my_account",
      "webhook_secret": "secret123",
      "risk_level": "Low",
      "preferred_indicators": ["RSI", "EMA"]
    }
    ```

    **주의**: AI 생성 전략은 반드시 백테스팅 후 사용하세요!
    """
    try:
        prompt = f"""
Create a TradingView Pine Script strategy based on this description:

Description: {request.description}
Risk Level: {request.risk_level}
Preferred Indicators: {request.preferred_indicators or 'Any'}

Requirements:
1. Use Pine Script v5
2. Include webhook alerts for auto-trading
3. Add proper risk management (stop loss/take profit)
4. Use account_id: {request.account_id}
5. Use webhook_secret: {request.webhook_secret}
6. Target symbol: BTCUSDT
7. Add clear comments in Korean

Generate complete Pine Script code.
"""

        # GPT-4로 전략 생성
        response = strategy_optimizer.openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert TradingView Pine Script developer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=2000
        )

        generated_code = response.choices[0].message.content

        # 코드 블록 추출
        import re
        code_match = re.search(r'```pine\n(.*?)\n```', generated_code, re.DOTALL)
        if code_match:
            generated_code = code_match.group(1)

        return {
            "success": True,
            "pine_script_code": generated_code,
            "description": request.description,
            "risk_level": request.risk_level,
            "warnings": [
                "⚠️ AI 생성 전략은 실험적 기능입니다.",
                "⚠️ 반드시 TradingView에서 백테스팅을 수행하세요.",
                "⚠️ Testnet에서 충분히 테스트 후 실전 적용하세요.",
                "⚠️ 손실 가능성을 충분히 인지하세요."
            ],
            "instructions": [
                "1. TradingView Pine Editor에 코드 붙여넣기",
                "2. 백테스팅 실행 (최소 6개월 이상 데이터)",
                "3. 성과 지표 확인 (Win Rate, Profit Factor, Sharpe Ratio)",
                "4. Testnet에서 실시간 테스트 (최소 1주일)",
                "5. 성과가 안정적이면 실전 적용"
            ]
        }

    except Exception as e:
        logger.error(f"Strategy generation failed: {str(e)}", exc_info=True)
        raise HTTPException(500, str(e))
