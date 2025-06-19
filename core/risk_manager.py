"""
리스크 관리 모듈

암호화폐 자동거래에서 리스크를 관리하고 포지션 크기를 계산하는 모듈입니다.
Kelly Criterion, Fixed Ratio, Volatility-based sizing 등 다양한 방법을 제공합니다.

Classes:
    RiskManager: 메인 리스크 관리 클래스
    PositionSizer: 포지션 크기 계산 클래스
    DrawdownManager: 손실폭 관리 클래스
    
Example:
    from core.risk_manager import RiskManager
    
    risk_manager = RiskManager(max_risk_per_trade=0.02)
    position_size = risk_manager.calculate_position_size(
        account_balance=1000,
        entry_price=50000,
        stop_loss=48000
    )
"""

from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class PositionSizingMethod(str, Enum):
    """포지션 크기 계산 방법 열거형."""
    FIXED_AMOUNT = "fixed_amount"
    FIXED_PERCENTAGE = "fixed_percentage"
    KELLY_CRITERION = "kelly_criterion"
    VOLATILITY_BASED = "volatility_based"
    ATR_BASED = "atr_based"


@dataclass
class RiskMetrics:
    """
    리스크 관련 지표를 저장하는 데이터 클래스.
    
    Attributes:
        max_drawdown (float): 최대 손실폭
        current_drawdown (float): 현재 손실폭
        win_rate (float): 승률
        profit_factor (float): 수익 팩터
        sharpe_ratio (float): 샤프 비율
        var_95 (float): 95% VaR (Value at Risk)
        expected_shortfall (float): 기대 손실
    """
    
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    sharpe_ratio: float = 0.0
    var_95: float = 0.0
    expected_shortfall: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """메트릭을 딕셔너리로 변환합니다."""
        return {
            'max_drawdown': self.max_drawdown,
            'current_drawdown': self.current_drawdown,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'sharpe_ratio': self.sharpe_ratio,
            'var_95': self.var_95,
            'expected_shortfall': self.expected_shortfall
        }


class RiskManager:
    """
    포괄적인 리스크 관리 클래스.
    
    포지션 크기 계산, 손실폭 관리, 리스크 지표 모니터링 등의 기능을 제공합니다.
    
    Attributes:
        max_risk_per_trade (float): 거래당 최대 리스크 비율
        max_portfolio_risk (float): 포트폴리오 전체 최대 리스크
        max_drawdown_limit (float): 최대 허용 손실폭
        position_sizing_method (PositionSizingMethod): 포지션 크기 계산 방법
        
    Methods:
        calculate_position_size(): 포지션 크기 계산
        check_risk_limits(): 리스크 한계 확인
        update_risk_metrics(): 리스크 지표 업데이트
        should_reduce_position(): 포지션 축소 필요성 판단
    """
    
    def __init__(
        self,
        max_risk_per_trade: float = 0.02,
        max_portfolio_risk: float = 0.10,
        max_drawdown_limit: float = 0.15,
        position_sizing_method: PositionSizingMethod = PositionSizingMethod.FIXED_PERCENTAGE
    ):
        """
        리스크 관리자 초기화.
        
        Args:
            max_risk_per_trade (float): 거래당 최대 리스크 (기본 2%)
            max_portfolio_risk (float): 포트폴리오 최대 리스크 (기본 10%)
            max_drawdown_limit (float): 최대 허용 손실폭 (기본 15%)
            position_sizing_method (PositionSizingMethod): 포지션 크기 계산 방법
        """
        self.max_risk_per_trade = max_risk_per_trade
        self.max_portfolio_risk = max_portfolio_risk
        self.max_drawdown_limit = max_drawdown_limit
        self.position_sizing_method = position_sizing_method
        
        # 리스크 지표 추적
        self.risk_metrics = RiskMetrics()
        self.trade_history: List[Dict[str, Any]] = []
        self.equity_curve: List[float] = []
        
        logger.info(f"리스크 관리자 초기화 완료 - 방법: {position_sizing_method}")
    
    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss: float,
        volatility: Optional[float] = None,
        win_rate: Optional[float] = None,
        avg_win: Optional[float] = None,
        avg_loss: Optional[float] = None
    ) -> float:
        """
        설정된 방법에 따라 포지션 크기를 계산합니다.
        
        Args:
            account_balance (float): 계좌 잔고
            entry_price (float): 진입 가격
            stop_loss (float): 손절매 가격
            volatility (float, optional): 변동성 (ATR 등)
            win_rate (float, optional): 승률 (Kelly Criterion용)
            avg_win (float, optional): 평균 수익 (Kelly Criterion용)
            avg_loss (float, optional): 평균 손실 (Kelly Criterion용)
            
        Returns:
            float: 계산된 포지션 크기 (USDT)
            
        Raises:
            ValueError: 잘못된 입력값이나 계산 불가능한 경우
        """
        try:
            if account_balance <= 0 or entry_price <= 0:
                raise ValueError("계좌 잔고와 진입 가격은 0보다 커야 합니다")
            
            if stop_loss <= 0 or stop_loss >= entry_price:
                raise ValueError("손절매 가격이 유효하지 않습니다")
            
            # 리스크 금액 계산 (거래당 최대 손실 금액)
            risk_amount = account_balance * self.max_risk_per_trade
            
            # 가격 차이 (리스크 per unit)
            price_diff = abs(entry_price - stop_loss)
            risk_per_unit = price_diff / entry_price
            
            if self.position_sizing_method == PositionSizingMethod.FIXED_AMOUNT:
                position_size = min(risk_amount, account_balance * 0.1)  # 최대 10%
                
            elif self.position_sizing_method == PositionSizingMethod.FIXED_PERCENTAGE:
                position_size = risk_amount / risk_per_unit
                
            elif self.position_sizing_method == PositionSizingMethod.KELLY_CRITERION:
                if win_rate is None or avg_win is None or avg_loss is None:
                    logger.warning("Kelly Criterion 계산에 필요한 파라미터 부족, Fixed Percentage 사용")
                    position_size = risk_amount / risk_per_unit
                else:
                    kelly_fraction = self._calculate_kelly_fraction(win_rate, avg_win, avg_loss)
                    # Kelly fraction의 25%만 사용 (보수적 접근)
                    position_size = account_balance * kelly_fraction * 0.25
                    
            elif self.position_sizing_method == PositionSizingMethod.VOLATILITY_BASED:
                if volatility is None:
                    logger.warning("변동성 데이터 없음, Fixed Percentage 사용")
                    position_size = risk_amount / risk_per_unit
                else:
                    # 변동성이 높을수록 포지션 크기 감소
                    volatility_adjustment = min(1.0, 0.02 / volatility)  # 2% 기준
                    position_size = (risk_amount / risk_per_unit) * volatility_adjustment
                    
            elif self.position_sizing_method == PositionSizingMethod.ATR_BASED:
                if volatility is None:  # ATR을 volatility로 사용
                    logger.warning("ATR 데이터 없음, Fixed Percentage 사용")
                    position_size = risk_amount / risk_per_unit
                else:
                    # ATR의 2배를 손절매 거리로 사용
                    atr_stop_distance = volatility * 2
                    atr_risk_per_unit = atr_stop_distance / entry_price
                    position_size = risk_amount / atr_risk_per_unit
            
            else:
                position_size = risk_amount / risk_per_unit
            
            # 최대/최소 포지션 크기 제한
            max_position = account_balance * 0.2  # 최대 20%
            min_position = 10.0  # 최소 10 USDT
            
            position_size = max(min_position, min(position_size, max_position))
            
            logger.info(
                f"포지션 크기 계산 완료 - 방법: {self.position_sizing_method}, "
                f"크기: {position_size:.2f} USDT, 리스크: {risk_amount:.2f} USDT"
            )
            
            return position_size
            
        except Exception as e:
            logger.error(f"포지션 크기 계산 중 오류: {e}")
            # 안전한 기본값 반환
            return account_balance * 0.01  # 1%
    
    def _calculate_kelly_fraction(self, win_rate: float, avg_win: float, avg_loss: float) -> float:
        """
        Kelly Criterion을 사용하여 최적 포지션 크기 비율을 계산합니다.
        
        Args:
            win_rate (float): 승률 (0.0 ~ 1.0)
            avg_win (float): 평균 수익률
            avg_loss (float): 평균 손실률 (양수)
            
        Returns:
            float: Kelly fraction (0.0 ~ 1.0)
        """
        try:
            if win_rate <= 0 or win_rate >= 1 or avg_win <= 0 or avg_loss <= 0:
                return 0.0
            
            # Kelly Fraction = (bp - q) / b
            # b = avg_win / avg_loss (승률 대비 손실률)
            # p = win_rate (승률)
            # q = 1 - p (패율)
            
            b = avg_win / avg_loss
            p = win_rate
            q = 1 - p
            
            kelly_fraction = (b * p - q) / b
            
            # 음수이거나 너무 큰 값 제한
            kelly_fraction = max(0.0, min(kelly_fraction, 0.25))  # 최대 25%
            
            return kelly_fraction
            
        except Exception as e:
            logger.error(f"Kelly Fraction 계산 오류: {e}")
            return 0.0
    
    def check_risk_limits(self, current_positions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        현재 포지션들의 리스크 한계를 확인합니다.
        
        Args:
            current_positions (List[Dict]): 현재 열린 포지션 리스트
            
        Returns:
            Dict[str, Any]: 리스크 체크 결과
        """
        try:
            total_risk = 0.0
            position_count = len(current_positions)
            
            for position in current_positions:
                position_risk = position.get('risk_amount', 0.0)
                total_risk += position_risk
            
            # 포트폴리오 리스크 비율 계산
            account_balance = sum(pos.get('account_balance', 0) for pos in current_positions)
            portfolio_risk_ratio = total_risk / account_balance if account_balance > 0 else 0
            
            # 현재 손실폭 계산
            current_drawdown = self.risk_metrics.current_drawdown
            
            risk_check = {
                'status': 'ok',
                'warnings': [],
                'total_risk': total_risk,
                'portfolio_risk_ratio': portfolio_risk_ratio,
                'position_count': position_count,
                'current_drawdown': current_drawdown
            }
            
            # 리스크 한계 확인
            if portfolio_risk_ratio > self.max_portfolio_risk:
                risk_check['status'] = 'warning'
                risk_check['warnings'].append(
                    f"포트폴리오 리스크 초과: {portfolio_risk_ratio:.2%} > {self.max_portfolio_risk:.2%}"
                )
            
            if current_drawdown > self.max_drawdown_limit:
                risk_check['status'] = 'critical'
                risk_check['warnings'].append(
                    f"최대 손실폭 초과: {current_drawdown:.2%} > {self.max_drawdown_limit:.2%}"
                )
            
            if position_count > 10:  # 최대 포지션 수 제한
                risk_check['status'] = 'warning'
                risk_check['warnings'].append(f"포지션 수 과다: {position_count} > 10")
            
            return risk_check
            
        except Exception as e:
            logger.error(f"리스크 한계 확인 중 오류: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def update_risk_metrics(self, trades_df: pd.DataFrame) -> RiskMetrics:
        """
        거래 내역을 바탕으로 리스크 지표를 업데이트합니다.
        
        Args:
            trades_df (pd.DataFrame): 거래 내역 데이터프레임
            
        Returns:
            RiskMetrics: 업데이트된 리스크 지표
        """
        try:
            if trades_df.empty:
                return self.risk_metrics
            
            # 기본 통계
            returns = trades_df['profit_ratio'].values
            winning_trades = returns[returns > 0]
            losing_trades = returns[returns < 0]
            
            # 승률 계산
            win_rate = len(winning_trades) / len(returns) if len(returns) > 0 else 0
            
            # 수익 팩터 계산
            gross_profit = winning_trades.sum() if len(winning_trades) > 0 else 0
            gross_loss = abs(losing_trades.sum()) if len(losing_trades) > 0 else 0
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # 샤프 비율 계산
            mean_return = returns.mean()
            std_return = returns.std()
            sharpe_ratio = mean_return / std_return if std_return > 0 else 0
            
            # 손실폭 계산
            cumulative_returns = (1 + pd.Series(returns)).cumprod()
            rolling_max = cumulative_returns.expanding().max()
            drawdown = (cumulative_returns - rolling_max) / rolling_max
            max_drawdown = abs(drawdown.min())
            current_drawdown = abs(drawdown.iloc[-1]) if len(drawdown) > 0 else 0
            
            # VaR 계산 (95% 신뢰수준)
            var_95 = np.percentile(returns, 5) if len(returns) > 0 else 0
            
            # Expected Shortfall (조건부 VaR)
            expected_shortfall = returns[returns <= var_95].mean() if len(returns[returns <= var_95]) > 0 else 0
            
            # 지표 업데이트
            self.risk_metrics = RiskMetrics(
                max_drawdown=max_drawdown,
                current_drawdown=current_drawdown,
                win_rate=win_rate,
                profit_factor=profit_factor,
                sharpe_ratio=sharpe_ratio,
                var_95=var_95,
                expected_shortfall=expected_shortfall
            )
            
            logger.info(f"리스크 지표 업데이트 완료 - 승률: {win_rate:.2%}, 최대손실폭: {max_drawdown:.2%}")
            
            return self.risk_metrics
            
        except Exception as e:
            logger.error(f"리스크 지표 업데이트 중 오류: {e}")
            return self.risk_metrics
    
    def should_reduce_position(self) -> Tuple[bool, str]:
        """
        현재 리스크 상황을 바탕으로 포지션 축소 필요성을 판단합니다.
        
        Returns:
            Tuple[bool, str]: (축소 필요 여부, 이유)
        """
        try:
            current_drawdown = self.risk_metrics.current_drawdown
            
            # 손실폭 기준 체크
            if current_drawdown > self.max_drawdown_limit * 0.8:  # 80% 도달시 경고
                return True, f"손실폭 위험 수준: {current_drawdown:.2%}"
            
            # 연속 손실 체크 (최근 거래 내역 확인)
            if len(self.trade_history) >= 5:
                recent_trades = self.trade_history[-5:]
                recent_losses = [t for t in recent_trades if t.get('profit_ratio', 0) < 0]
                
                if len(recent_losses) >= 4:  # 5거래 중 4거래 손실
                    return True, "연속 손실 발생"
            
            # 변동성 급증 체크 (구현 필요시)
            # 시장 상황 악화 체크 (구현 필요시)
            
            return False, "정상 범위"
            
        except Exception as e:
            logger.error(f"포지션 축소 판단 중 오류: {e}")
            return False, "판단 불가"
    
    def add_trade_record(self, trade_data: Dict[str, Any]) -> None:
        """
        거래 기록을 추가합니다.
        
        Args:
            trade_data (Dict[str, Any]): 거래 데이터
        """
        try:
            self.trade_history.append(trade_data)
            
            # 최근 1000개 거래만 유지
            if len(self.trade_history) > 1000:
                self.trade_history = self.trade_history[-1000:]
            
            # 자산 곡선 업데이트
            profit_ratio = trade_data.get('profit_ratio', 0)
            if self.equity_curve:
                new_equity = self.equity_curve[-1] * (1 + profit_ratio)
            else:
                new_equity = 1.0 + profit_ratio
            
            self.equity_curve.append(new_equity)
            
        except Exception as e:
            logger.error(f"거래 기록 추가 중 오류: {e}")


class DrawdownManager:
    """손실폭 전용 관리 클래스."""
    
    def __init__(self, max_drawdown_limit: float = 0.15):
        self.max_drawdown_limit = max_drawdown_limit
        self.equity_curve: List[float] = [1.0]  # 시작 자산을 1.0으로 정규화
        self.peak_equity = 1.0
        
    def update_equity(self, new_equity: float) -> Dict[str, float]:
        """
        자산 곡선을 업데이트하고 손실폭을 계산합니다.
        
        Args:
            new_equity (float): 새로운 자산 가치
            
        Returns:
            Dict[str, float]: 손실폭 관련 지표
        """
        self.equity_curve.append(new_equity)
        
        # 새로운 최고점 확인
        if new_equity > self.peak_equity:
            self.peak_equity = new_equity
        
        # 현재 손실폭 계산
        current_drawdown = (self.peak_equity - new_equity) / self.peak_equity
        
        # 최대 손실폭 계산
        equity_series = pd.Series(self.equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown_series = (equity_series - rolling_max) / rolling_max
        max_drawdown = abs(drawdown_series.min())
        
        return {
            'current_drawdown': current_drawdown,
            'max_drawdown': max_drawdown,
            'peak_equity': self.peak_equity,
            'current_equity': new_equity
        }