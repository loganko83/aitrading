"""
Pine Script Analyzer Service

Features:
- Pine Script 코드 파싱 및 분석
- 전략 성과 지표 추출
- 파라미터 최적화 추천
- AI 기반 코드 품질 평가
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import openai
from anthropic import Anthropic

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class StrategyMetrics:
    """전략 성과 지표"""
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown: Optional[float] = None
    total_trades: Optional[int] = None
    avg_trade: Optional[float] = None
    risk_reward_ratio: Optional[float] = None


@dataclass
class StrategyInfo:
    """전략 정보"""
    name: str
    version: int
    description: str
    indicators: List[str]
    parameters: Dict[str, Any]
    entry_conditions: List[str]
    exit_conditions: List[str]
    risk_management: Dict[str, Any]
    has_webhook: bool
    metrics: Optional[StrategyMetrics] = None


class PineScriptAnalyzer:
    """Pine Script 분석기"""

    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
        self.anthropic_client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def parse_pine_script(self, code: str) -> StrategyInfo:
        """
        Pine Script 코드를 파싱하여 전략 정보 추출

        Args:
            code: Pine Script 소스 코드

        Returns:
            전략 정보 객체
        """
        logger.info("Parsing Pine Script...")

        # 버전 추출
        version_match = re.search(r'//@version=(\d+)', code)
        version = int(version_match.group(1)) if version_match else 4

        # 전략명 추출
        strategy_match = re.search(r'strategy\("([^"]+)"', code)
        name = strategy_match.group(1) if strategy_match else "Unknown Strategy"

        # 주석에서 설명 추출
        description_lines = re.findall(r'//\s*(.+)', code[:500])
        description = " ".join(description_lines[:3]) if description_lines else ""

        # 인디케이터 추출
        indicators = self._extract_indicators(code)

        # 파라미터 추출
        parameters = self._extract_parameters(code)

        # 진입/청산 조건 추출
        entry_conditions = self._extract_entry_conditions(code)
        exit_conditions = self._extract_exit_conditions(code)

        # 리스크 관리 추출
        risk_management = self._extract_risk_management(code)

        # Webhook 존재 여부
        has_webhook = "alert(" in code and "webhook" in code.lower()

        return StrategyInfo(
            name=name,
            version=version,
            description=description,
            indicators=indicators,
            parameters=parameters,
            entry_conditions=entry_conditions,
            exit_conditions=exit_conditions,
            risk_management=risk_management,
            has_webhook=has_webhook
        )

    def _extract_indicators(self, code: str) -> List[str]:
        """인디케이터 추출"""
        indicators = []

        indicator_patterns = {
            "EMA": r'ta\.ema\(',
            "SMA": r'ta\.sma\(',
            "RSI": r'ta\.rsi\(',
            "MACD": r'ta\.macd\(',
            "Bollinger Bands": r'ta\.bb\(',
            "ATR": r'ta\.atr\(',
            "Stochastic": r'ta\.stoch\(',
            "ADX": r'ta\.adx\(',
            "Volume": r'volume',
            "SuperTrend": r'supertrend\(',
        }

        for name, pattern in indicator_patterns.items():
            if re.search(pattern, code):
                indicators.append(name)

        return indicators

    def _extract_parameters(self, code: str) -> Dict[str, Any]:
        """파라미터 추출"""
        parameters = {}

        # input.int, input.float, input.string, input.bool 추출
        input_patterns = [
            (r'input\.int\((\d+),\s*"([^"]+)"', int),
            (r'input\.float\(([\d.]+),\s*"([^"]+)"', float),
            (r'input\.string\("([^"]+)",\s*"([^"]+)"', str),
            (r'input\.bool\((true|false),\s*"([^"]+)"', bool)
        ]

        for pattern, dtype in input_patterns:
            matches = re.findall(pattern, code)
            for match in matches:
                if len(match) == 2:
                    value, name = match
                    if dtype == bool:
                        value = value == "true"
                    elif dtype != str:
                        value = dtype(value)
                    parameters[name] = value

        return parameters

    def _extract_entry_conditions(self, code: str) -> List[str]:
        """진입 조건 추출"""
        conditions = []

        # strategy.entry 직전 조건문 찾기
        entry_blocks = re.findall(
            r'if\s+\(([^)]+)\)\s+strategy\.entry',
            code,
            re.MULTILINE
        )

        for condition in entry_blocks:
            # 변수명을 읽기 쉽게 정리
            cleaned = condition.strip().replace('\n', ' ')
            conditions.append(cleaned)

        return conditions

    def _extract_exit_conditions(self, code: str) -> List[str]:
        """청산 조건 추출"""
        conditions = []

        # strategy.close, strategy.exit 직전 조건문 찾기
        exit_blocks = re.findall(
            r'if\s+\(([^)]+)\)\s+strategy\.(close|exit)',
            code,
            re.MULTILINE
        )

        for condition, _ in exit_blocks:
            cleaned = condition.strip().replace('\n', ' ')
            conditions.append(cleaned)

        return conditions

    def _extract_risk_management(self, code: str) -> Dict[str, Any]:
        """리스크 관리 설정 추출"""
        risk_mgmt = {}

        # Stop Loss
        stop_loss_match = re.search(r'stop\s*=\s*([^,\n]+)', code)
        if stop_loss_match:
            risk_mgmt["stop_loss"] = stop_loss_match.group(1).strip()

        # Take Profit
        take_profit_match = re.search(r'limit\s*=\s*([^,\n]+)', code)
        if take_profit_match:
            risk_mgmt["take_profit"] = take_profit_match.group(1).strip()

        # Position Sizing
        qty_match = re.search(r'qty\s*=\s*([^,\n]+)', code)
        if qty_match:
            risk_mgmt["position_size"] = qty_match.group(1).strip()

        return risk_mgmt

    async def analyze_with_ai(self, code: str, strategy_info: StrategyInfo) -> Dict[str, Any]:
        """
        AI를 활용한 전략 분석 (GPT-4 + Claude)

        Args:
            code: Pine Script 코드
            strategy_info: 파싱된 전략 정보

        Returns:
            AI 분석 결과
        """
        logger.info("Analyzing strategy with AI ensemble...")

        # GPT-4 분석
        gpt4_analysis = await self._analyze_with_gpt4(code, strategy_info)

        # Claude 분석
        claude_analysis = await self._analyze_with_claude(code, strategy_info)

        # 결과 통합
        combined_analysis = {
            "gpt4": gpt4_analysis,
            "claude": claude_analysis,
            "consensus": self._combine_analyses(gpt4_analysis, claude_analysis),
            "timestamp": datetime.utcnow().isoformat()
        }

        return combined_analysis

    async def _analyze_with_gpt4(self, code: str, strategy_info: StrategyInfo) -> Dict[str, Any]:
        """GPT-4로 전략 분석"""
        try:
            prompt = f"""
Analyze this TradingView Pine Script strategy and provide insights:

Strategy Name: {strategy_info.name}
Indicators: {', '.join(strategy_info.indicators)}
Parameters: {strategy_info.parameters}

Code:
```pine
{code[:2000]}  # 처음 2000자만 전송
```

Please analyze:
1. Strategy Quality (0-100 score)
2. Strengths (top 3)
3. Weaknesses (top 3)
4. Recommended Improvements
5. Risk Level (Low/Medium/High)
6. Best Market Conditions (Trending/Ranging/Volatile)
7. Suggested Parameter Optimizations

Respond in JSON format.
"""

            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional trading strategy analyst."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )

            result = response.choices[0].message.content

            # JSON 파싱 시도
            import json
            try:
                return json.loads(result)
            except:
                return {"raw_response": result}

        except Exception as e:
            logger.error(f"GPT-4 analysis failed: {str(e)}")
            return {"error": str(e)}

    async def _analyze_with_claude(self, code: str, strategy_info: StrategyInfo) -> Dict[str, Any]:
        """Claude로 전략 분석"""
        try:
            prompt = f"""
Analyze this TradingView Pine Script strategy:

Strategy: {strategy_info.name}
Indicators: {', '.join(strategy_info.indicators)}
Entry Conditions: {strategy_info.entry_conditions}
Exit Conditions: {strategy_info.exit_conditions}

Code:
```pine
{code[:2000]}
```

Provide:
1. Code Quality Score (0-100)
2. Top 3 Strengths
3. Top 3 Risks
4. Optimization Recommendations
5. Market Suitability
6. Edge Analysis

Format: JSON
"""

            response = self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.3,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            result = response.content[0].text

            # JSON 파싱 시도
            import json
            try:
                return json.loads(result)
            except:
                return {"raw_response": result}

        except Exception as e:
            logger.error(f"Claude analysis failed: {str(e)}")
            return {"error": str(e)}

    def _combine_analyses(self, gpt4: Dict, claude: Dict) -> Dict[str, Any]:
        """두 AI 분석 결과 통합"""
        consensus = {}

        # 평균 품질 점수
        gpt4_score = gpt4.get("quality_score", 0)
        claude_score = claude.get("code_quality_score", 0)

        if gpt4_score and claude_score:
            consensus["average_quality_score"] = (gpt4_score + claude_score) / 2

        # 공통 강점
        gpt4_strengths = set(gpt4.get("strengths", []))
        claude_strengths = set(claude.get("strengths", []))
        consensus["common_strengths"] = list(gpt4_strengths & claude_strengths)

        # 공통 약점
        gpt4_weaknesses = set(gpt4.get("weaknesses", []))
        claude_risks = set(claude.get("risks", []))
        consensus["common_concerns"] = list(gpt4_weaknesses & claude_risks)

        # 종합 추천사항
        all_recommendations = []
        all_recommendations.extend(gpt4.get("recommended_improvements", []))
        all_recommendations.extend(claude.get("optimization_recommendations", []))
        consensus["combined_recommendations"] = all_recommendations[:5]

        return consensus

    def extract_backtest_results(self, code: str, html_results: Optional[str] = None) -> StrategyMetrics:
        """
        백테스팅 결과 추출 (Pine Script 주석 또는 HTML)

        Args:
            code: Pine Script 코드
            html_results: TradingView 백테스트 결과 HTML (선택)

        Returns:
            전략 성과 지표
        """
        metrics = StrategyMetrics()

        # Pine Script 주석에서 성과 추출
        if html_results:
            # HTML 파싱 (간단한 정규식 사용)
            win_rate = re.search(r'Win Rate[:\s]+(\d+\.?\d*)%', html_results)
            if win_rate:
                metrics.win_rate = float(win_rate.group(1))

            profit_factor = re.search(r'Profit Factor[:\s]+(\d+\.?\d*)', html_results)
            if profit_factor:
                metrics.profit_factor = float(profit_factor.group(1))

            sharpe = re.search(r'Sharpe Ratio[:\s]+(\d+\.?\d*)', html_results)
            if sharpe:
                metrics.sharpe_ratio = float(sharpe.group(1))

            drawdown = re.search(r'Max Drawdown[:\s]+(\d+\.?\d*)%', html_results)
            if drawdown:
                metrics.max_drawdown = float(drawdown.group(1))

        return metrics


# 싱글톤 인스턴스
pine_analyzer = PineScriptAnalyzer()
