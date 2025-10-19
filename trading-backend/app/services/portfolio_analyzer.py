"""
Portfolio Analysis Service

포트폴리오 분석 서비스:
- 상관관계 계산 (Correlation Analysis)
- 리밸런싱 알고리즘 (Rebalancing Algorithm)
- VaR 계산 (Value at Risk)
- 리스크 지표 (MDD, Sharpe Ratio, etc.)
"""

import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)


class PortfolioAnalyzer:
    """포트폴리오 분석 서비스"""

    def __init__(self):
        self.logger = logger

    def calculate_correlation_matrix(
        self,
        price_data: Dict[str, List[float]]
    ) -> Dict[str, Dict[str, float]]:
        """
        상관관계 매트릭스 계산

        Args:
            price_data: {symbol: [prices]} 형식의 가격 데이터

        Returns:
            상관관계 매트릭스 {symbol1: {symbol2: correlation}}
        """
        try:
            if not price_data or len(price_data) < 2:
                raise ValueError("At least 2 symbols required for correlation analysis")

            # DataFrame 생성
            df = pd.DataFrame(price_data)

            # 가격 변동률 계산
            returns = df.pct_change().dropna()

            # 상관관계 계산
            corr_matrix = returns.corr()

            # Dictionary 형식으로 변환
            result = {}
            for symbol1 in corr_matrix.index:
                result[symbol1] = {}
                for symbol2 in corr_matrix.columns:
                    result[symbol1][symbol2] = round(float(corr_matrix.loc[symbol1, symbol2]), 4)

            self.logger.info(f"Correlation matrix calculated for {len(price_data)} symbols")
            return result

        except Exception as e:
            self.logger.error(f"Failed to calculate correlation matrix: {str(e)}")
            raise

    def calculate_portfolio_var(
        self,
        positions: List[Dict[str, Any]],
        confidence_level: float = 0.95,
        time_horizon_days: int = 1
    ) -> Dict[str, float]:
        """
        포트폴리오 VaR (Value at Risk) 계산
        Historical Simulation 방법 사용

        Args:
            positions: 포지션 리스트 [{symbol, size, entry_price, current_price}]
            confidence_level: 신뢰 수준 (default: 0.95 = 95%)
            time_horizon_days: 시간 범위 (default: 1 = 1일)

        Returns:
            VaR 계산 결과 {var_amount, var_percentage, confidence_level}
        """
        try:
            if not positions:
                return {
                    "var_amount": 0.0,
                    "var_percentage": 0.0,
                    "confidence_level": confidence_level,
                    "time_horizon_days": time_horizon_days
                }

            # 포트폴리오 총 가치 계산
            total_value = sum(
                abs(pos.get("size", 0)) * pos.get("current_price", 0)
                for pos in positions
            )

            if total_value == 0:
                return {
                    "var_amount": 0.0,
                    "var_percentage": 0.0,
                    "confidence_level": confidence_level,
                    "time_horizon_days": time_horizon_days
                }

            # 각 포지션의 손익률 계산
            position_returns = []
            for pos in positions:
                entry_price = pos.get("entry_price", 0)
                current_price = pos.get("current_price", 0)

                if entry_price > 0:
                    pnl_pct = ((current_price - entry_price) / entry_price) * 100

                    # 숏 포지션은 반대
                    if pos.get("side") == "SHORT":
                        pnl_pct = -pnl_pct

                    position_returns.append(pnl_pct)

            if not position_returns:
                return {
                    "var_amount": 0.0,
                    "var_percentage": 0.0,
                    "confidence_level": confidence_level,
                    "time_horizon_days": time_horizon_days
                }

            # VaR 계산 (percentile 방법)
            var_percentile = (1 - confidence_level) * 100
            var_percentage = np.percentile(position_returns, var_percentile)
            var_amount = (abs(var_percentage) / 100) * total_value

            # 시간 범위 조정 (Square Root of Time)
            var_amount_adjusted = var_amount * np.sqrt(time_horizon_days)
            var_percentage_adjusted = var_percentage * np.sqrt(time_horizon_days)

            result = {
                "var_amount": round(var_amount_adjusted, 2),
                "var_percentage": round(abs(var_percentage_adjusted), 2),
                "confidence_level": confidence_level,
                "time_horizon_days": time_horizon_days,
                "portfolio_value": round(total_value, 2)
            }

            self.logger.info(f"VaR calculated: ${result['var_amount']} ({result['var_percentage']}%)")
            return result

        except Exception as e:
            self.logger.error(f"Failed to calculate VaR: {str(e)}")
            raise

    def calculate_max_drawdown(
        self,
        equity_curve: List[float]
    ) -> Dict[str, float]:
        """
        최대 손실폭 (MDD - Maximum Drawdown) 계산

        Args:
            equity_curve: 자산 곡선 (시간 순서)

        Returns:
            MDD 정보 {mdd_percentage, mdd_amount, peak_value, trough_value}
        """
        try:
            if not equity_curve or len(equity_curve) < 2:
                return {
                    "mdd_percentage": 0.0,
                    "mdd_amount": 0.0,
                    "peak_value": 0.0,
                    "trough_value": 0.0
                }

            equity_array = np.array(equity_curve)

            # Running maximum (누적 최대값)
            running_max = np.maximum.accumulate(equity_array)

            # Drawdown 계산
            drawdown = (equity_array - running_max) / running_max * 100

            # 최대 손실폭
            mdd_percentage = float(np.min(drawdown))
            mdd_idx = int(np.argmin(drawdown))

            # Peak와 Trough 값
            peak_idx = int(np.argmax(equity_array[:mdd_idx + 1]))
            peak_value = float(equity_array[peak_idx])
            trough_value = float(equity_array[mdd_idx])
            mdd_amount = peak_value - trough_value

            result = {
                "mdd_percentage": round(mdd_percentage, 2),
                "mdd_amount": round(mdd_amount, 2),
                "peak_value": round(peak_value, 2),
                "trough_value": round(trough_value, 2)
            }

            self.logger.info(f"MDD calculated: {result['mdd_percentage']}%")
            return result

        except Exception as e:
            self.logger.error(f"Failed to calculate MDD: {str(e)}")
            raise

    def calculate_sharpe_ratio(
        self,
        returns: List[float],
        risk_free_rate: float = 0.02
    ) -> float:
        """
        샤프 비율 (Sharpe Ratio) 계산

        Args:
            returns: 수익률 리스트 (백분율)
            risk_free_rate: 무위험 수익률 (연간, default: 2%)

        Returns:
            샤프 비율
        """
        try:
            if not returns or len(returns) < 2:
                return 0.0

            returns_array = np.array(returns)

            # 평균 수익률
            mean_return = np.mean(returns_array)

            # 표준편차 (변동성)
            std_return = np.std(returns_array, ddof=1)

            if std_return == 0:
                return 0.0

            # 샤프 비율 = (평균 수익률 - 무위험 수익률) / 표준편차
            # 일간 무위험 수익률로 변환
            daily_risk_free = (1 + risk_free_rate) ** (1/252) - 1
            daily_risk_free_pct = daily_risk_free * 100

            sharpe = (mean_return - daily_risk_free_pct) / std_return

            # 연간화 (252 거래일 가정)
            sharpe_annual = sharpe * np.sqrt(252)

            self.logger.info(f"Sharpe Ratio calculated: {round(sharpe_annual, 2)}")
            return round(sharpe_annual, 2)

        except Exception as e:
            self.logger.error(f"Failed to calculate Sharpe Ratio: {str(e)}")
            raise

    def calculate_rebalancing_orders(
        self,
        current_allocation: Dict[str, float],
        target_allocation: Dict[str, float],
        portfolio_value: float,
        current_prices: Dict[str, float],
        min_order_value: float = 10.0
    ) -> List[Dict[str, Any]]:
        """
        리밸런싱 주문 계산

        Args:
            current_allocation: 현재 배분 {symbol: percentage}
            target_allocation: 목표 배분 {symbol: percentage}
            portfolio_value: 포트폴리오 총 가치 (USDT)
            current_prices: 현재 가격 {symbol: price}
            min_order_value: 최소 주문 금액 (USDT)

        Returns:
            리밸런싱 주문 리스트 [{symbol, action, percentage_diff, target_value, quantity}]
        """
        try:
            orders = []

            # 모든 심볼 통합
            all_symbols = set(current_allocation.keys()) | set(target_allocation.keys())

            for symbol in all_symbols:
                current_pct = current_allocation.get(symbol, 0.0)
                target_pct = target_allocation.get(symbol, 0.0)

                # 차이 계산
                diff_pct = target_pct - current_pct

                # 최소 임계값 (0.5% 이상 차이만 처리)
                if abs(diff_pct) < 0.5:
                    continue

                # 목표 금액
                target_value = (target_pct / 100) * portfolio_value
                current_value = (current_pct / 100) * portfolio_value
                diff_value = target_value - current_value

                # 최소 주문 금액 체크
                if abs(diff_value) < min_order_value:
                    continue

                # 주문 액션
                action = "BUY" if diff_value > 0 else "SELL"

                # 수량 계산
                price = current_prices.get(symbol, 0)
                if price == 0:
                    self.logger.warning(f"Price not available for {symbol}, skipping")
                    continue

                quantity = abs(diff_value) / price

                order = {
                    "symbol": symbol,
                    "action": action,
                    "percentage_diff": round(diff_pct, 2),
                    "current_percentage": round(current_pct, 2),
                    "target_percentage": round(target_pct, 2),
                    "current_value": round(current_value, 2),
                    "target_value": round(target_value, 2),
                    "diff_value": round(diff_value, 2),
                    "price": round(price, 2),
                    "quantity": round(quantity, 6)
                }

                orders.append(order)

            # 차이가 큰 순으로 정렬
            orders.sort(key=lambda x: abs(x["percentage_diff"]), reverse=True)

            self.logger.info(f"Rebalancing orders calculated: {len(orders)} orders")
            return orders

        except Exception as e:
            self.logger.error(f"Failed to calculate rebalancing orders: {str(e)}")
            raise

    def calculate_position_concentration(
        self,
        positions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        포지션 집중도 분석

        Args:
            positions: 포지션 리스트

        Returns:
            집중도 분석 결과
        """
        try:
            if not positions:
                return {
                    "total_positions": 0,
                    "largest_position_pct": 0.0,
                    "top_3_concentration": 0.0,
                    "herfindahl_index": 0.0,
                    "diversification_ratio": 0.0
                }

            # 포지션 가치 계산
            total_value = 0
            position_values = []

            for pos in positions:
                size = abs(pos.get("size", 0))
                price = pos.get("current_price", 0)
                value = size * price

                total_value += value
                position_values.append(value)

            if total_value == 0:
                return {
                    "total_positions": len(positions),
                    "largest_position_pct": 0.0,
                    "top_3_concentration": 0.0,
                    "herfindahl_index": 0.0,
                    "diversification_ratio": 0.0
                }

            # 비율 계산
            position_pcts = [(v / total_value) * 100 for v in position_values]
            position_pcts_sorted = sorted(position_pcts, reverse=True)

            # 최대 포지션 비율
            largest_pct = position_pcts_sorted[0]

            # Top 3 집중도
            top_3_concentration = sum(position_pcts_sorted[:3])

            # Herfindahl-Hirschman Index (HHI)
            # 0 = 완전 분산, 10000 = 완전 집중
            hhi = sum(p ** 2 for p in position_pcts)

            # 다각화 비율 (1 / HHI의 제곱근)
            # 1 = 완전 집중, N = 완전 분산 (N = 포지션 수)
            diversification_ratio = 1 / np.sqrt(hhi / 10000) if hhi > 0 else 0

            result = {
                "total_positions": len(positions),
                "largest_position_pct": round(largest_pct, 2),
                "top_3_concentration": round(top_3_concentration, 2),
                "herfindahl_index": round(hhi, 2),
                "diversification_ratio": round(diversification_ratio, 2),
                "total_value": round(total_value, 2)
            }

            self.logger.info(f"Position concentration analyzed: {result['total_positions']} positions")
            return result

        except Exception as e:
            self.logger.error(f"Failed to calculate position concentration: {str(e)}")
            raise

    def calculate_liquidation_prices(
        self,
        positions: List[Dict[str, Any]],
        maintenance_margin_rate: float = 0.004
    ) -> List[Dict[str, Any]]:
        """
        청산 가격 계산

        Args:
            positions: 포지션 리스트
            maintenance_margin_rate: 유지 증거금 비율 (default: 0.4% = 0.004)

        Returns:
            청산 가격 정보 리스트
        """
        try:
            liquidation_info = []

            for pos in positions:
                symbol = pos.get("symbol", "UNKNOWN")
                side = pos.get("side", "LONG")
                entry_price = pos.get("entry_price", 0)
                leverage = pos.get("leverage", 1)
                size = abs(pos.get("size", 0))

                if entry_price == 0 or leverage == 0:
                    continue

                # 청산 가격 계산
                if side == "LONG":
                    # 롱: 청산가 = 진입가 * (1 - 1/레버리지 + 유지증거금률)
                    liq_price = entry_price * (1 - (1 / leverage) + maintenance_margin_rate)
                else:
                    # 숏: 청산가 = 진입가 * (1 + 1/레버리지 - 유지증거금률)
                    liq_price = entry_price * (1 + (1 / leverage) - maintenance_margin_rate)

                # 현재 가격과의 거리
                current_price = pos.get("current_price", entry_price)
                distance_pct = ((liq_price - current_price) / current_price) * 100

                info = {
                    "symbol": symbol,
                    "side": side,
                    "entry_price": round(entry_price, 2),
                    "current_price": round(current_price, 2),
                    "liquidation_price": round(liq_price, 2),
                    "distance_percentage": round(abs(distance_pct), 2),
                    "leverage": leverage,
                    "size": round(size, 6)
                }

                liquidation_info.append(info)

            self.logger.info(f"Liquidation prices calculated for {len(liquidation_info)} positions")
            return liquidation_info

        except Exception as e:
            self.logger.error(f"Failed to calculate liquidation prices: {str(e)}")
            raise


# Global instance
portfolio_analyzer = PortfolioAnalyzer()
