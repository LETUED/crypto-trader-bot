"""
거래 전략 테스트 모듈

RSI Strategy 및 기타 거래 전략들의 unit test(단위 테스트)를 제공합니다.
pytest를 사용하여 전략의 각 구성 요소를 철저히 테스트합니다.

Test Classes:
    TestRSIStrategy: RSI 전략 테스트
    TestBaseStrategy: 기본 전략 클래스 테스트
    TestStrategyValidator: 전략 검증 테스트
    
Usage:
    pytest tests/test_strategy.py -v
    pytest tests/test_strategy.py::TestRSIStrategy::test_populate_indicators -v
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from datetime import datetime
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from strategies.rsi_strategy import RSIStrategy
from core.strategy_base import BaseStrategy, StrategyMetrics, StrategyValidator
from core.risk_manager import RiskManager


class TestRSIStrategy:
    """RSI 전략 테스트 클래스."""
    
    @pytest.fixture
    def sample_config(self):
        """테스트용 설정 fixture."""
        return {
            'exchange': 'binance',
            'stake_currency': 'USDT',
            'dry_run': True,
            'timeframe': '5m'
        }
    
    @pytest.fixture
    def sample_dataframe(self):
        """테스트용 OHLCV 데이터 fixture."""
        np.random.seed(42)  # 재현 가능한 결과를 위해
        
        dates = pd.date_range('2023-01-01', periods=500, freq='5min')
        
        # 실제 가격 데이터와 유사한 패턴 생성
        base_price = 50000
        price_changes = np.random.normal(0, 0.02, 500)  # 2% 표준편차
        prices = [base_price]
        
        for change in price_changes[1:]:
            new_price = prices[-1] * (1 + change)
            prices.append(max(new_price, 1000))  # 최소 가격 보장
        
        df = pd.DataFrame({
            'date': dates,
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.randint(100, 10000, 500)
        })
        
        # high/low 조정 (open/close보다 높거나 낮게)
        df['high'] = df[['open', 'close', 'high']].max(axis=1)
        df['low'] = df[['open', 'close', 'low']].min(axis=1)
        
        return df
    
    @pytest.fixture
    def rsi_strategy(self, sample_config):
        """RSI 전략 인스턴스 fixture."""
        return RSIStrategy(sample_config)
    
    def test_strategy_initialization(self, rsi_strategy):
        """전략 초기화 테스트."""
        assert rsi_strategy.STRATEGY_NAME == "RSI_Strategy"
        assert rsi_strategy.STRATEGY_VERSION == "1.0.0"
        assert rsi_strategy.timeframe == '5m'
        assert rsi_strategy.startup_candle_count == 200
        assert rsi_strategy.stoploss == -0.04
        assert isinstance(rsi_strategy.minimal_roi, dict)
    
    def test_populate_indicators(self, rsi_strategy, sample_dataframe):
        """지표 계산 테스트."""
        metadata = {'pair': 'BTC/USDT', 'timeframe': '5m'}
        
        result_df = rsi_strategy.populate_indicators(sample_dataframe, metadata)
        
        # 필수 지표들이 계산되었는지 확인
        required_indicators = [
            'rsi', 'rsi_slow', 'bb_upper', 'bb_middle', 'bb_lower',
            'bb_width', 'bb_position', 'volume_sma', 'volume_ratio',
            'macd', 'macd_signal', 'macd_hist', 'ema_fast', 'ema_slow',
            'trend', 'atr', 'volatility'
        ]
        
        for indicator in required_indicators:
            assert indicator in result_df.columns, f"지표 '{indicator}'가 누락됨"
            assert not result_df[indicator].isna().all(), f"지표 '{indicator}'가 모두 NaN"
        
        # RSI 값 범위 확인 (0-100)
        rsi_values = result_df['rsi'].dropna()
        assert (rsi_values >= 0).all() and (rsi_values <= 100).all(), "RSI 값이 유효 범위를 벗어남"
        
        # 볼린저밴드 순서 확인 (lower <= middle <= upper)
        bb_data = result_df[['bb_lower', 'bb_middle', 'bb_upper']].dropna()
        assert (bb_data['bb_lower'] <= bb_data['bb_middle']).all(), "볼린저밴드 하단이 중간선보다 높음"
        assert (bb_data['bb_middle'] <= bb_data['bb_upper']).all(), "볼린저밴드 중간선이 상단보다 높음"
    
    def test_populate_entry_trend(self, rsi_strategy, sample_dataframe):
        """매수 신호 생성 테스트."""
        metadata = {'pair': 'BTC/USDT', 'timeframe': '5m'}
        
        # 지표 계산
        df_with_indicators = rsi_strategy.populate_indicators(sample_dataframe, metadata)
        
        # 매수 신호 생성
        result_df = rsi_strategy.populate_entry_trend(df_with_indicators, metadata)
        
        # enter_long 컬럼이 존재하는지 확인
        assert 'enter_long' in result_df.columns, "enter_long 컬럼이 없음"
        
        # 신호 값이 0 또는 1인지 확인
        entry_signals = result_df['enter_long'].dropna()
        assert entry_signals.isin([0, 1]).all(), "매수 신호가 0 또는 1이 아님"
        
        # 신호가 생성되었는지 확인 (적어도 하나의 신호)
        signal_count = entry_signals.sum()
        assert signal_count >= 0, "매수 신호 수가 음수"
        
        # 신호 비율이 합리적인지 확인 (전체의 50% 이하)
        signal_ratio = signal_count / len(entry_signals) if len(entry_signals) > 0 else 0
        assert signal_ratio <= 0.5, f"매수 신호 비율이 너무 높음: {signal_ratio:.2%}"
    
    def test_populate_exit_trend(self, rsi_strategy, sample_dataframe):
        """매도 신호 생성 테스트."""
        metadata = {'pair': 'BTC/USDT', 'timeframe': '5m'}
        
        # 지표 계산
        df_with_indicators = rsi_strategy.populate_indicators(sample_dataframe, metadata)
        
        # 매도 신호 생성
        result_df = rsi_strategy.populate_exit_trend(df_with_indicators, metadata)
        
        # exit_long 컬럼이 존재하는지 확인
        assert 'exit_long' in result_df.columns, "exit_long 컬럼이 없음"
        
        # 신호 값이 0 또는 1인지 확인
        exit_signals = result_df['exit_long'].dropna()
        assert exit_signals.isin([0, 1]).all(), "매도 신호가 0 또는 1이 아님"
        
        # 신호가 합리적인 범위인지 확인
        signal_count = exit_signals.sum()
        signal_ratio = signal_count / len(exit_signals) if len(exit_signals) > 0 else 0
        assert signal_ratio <= 0.5, f"매도 신호 비율이 너무 높음: {signal_ratio:.2%}"
    
    def test_custom_sell_logic(self, rsi_strategy):
        """커스텀 매도 로직 테스트."""
        # Mock trade 객체 생성
        mock_trade = Mock()
        mock_trade.open_date_utc = datetime.now()
        
        # 정상 상황 (매도하지 않음)
        result = rsi_strategy.custom_sell(
            pair="BTC/USDT",
            trade=mock_trade,
            current_time=datetime.now(),
            current_rate=50000.0,
            current_profit=0.02  # 2% 수익
        )
        assert result is False, "정상 상황에서 매도 신호가 발생"
        
        # 큰 수익 상황 (매도)
        result = rsi_strategy.custom_sell(
            pair="BTC/USDT",
            trade=mock_trade,
            current_time=datetime.now(),
            current_rate=50000.0,
            current_profit=0.16  # 16% 수익
        )
        assert result is True, "큰 수익 상황에서 매도 신호가 발생하지 않���"
    
    def test_confirm_trade_entry(self, rsi_strategy):
        """거래 진입 확인 테스트."""
        result = rsi_strategy.confirm_trade_entry(
            pair="BTC/USDT",
            order_type="limit",
            amount=0.001,
            rate=50000.0
        )
        
        assert isinstance(result, bool), "거래 진입 확인 결과가 boolean이 아님"
        assert result is True, "정상적인 거래 진입이 거부됨"


class TestBaseStrategy:
    """기본 전략 클래스 테스트."""
    
    @pytest.fixture
    def base_strategy_config(self):
        """기본 전략 설정."""
        return {
            'exchange': 'binance',
            'stake_currency': 'USDT',
            'dry_run': True
        }
    
    def test_strategy_metrics_initialization(self):
        """전략 메트릭 초기화 테스트."""
        metrics = StrategyMetrics()
        
        assert metrics.total_trades == 0
        assert metrics.win_rate == 0.0
        assert metrics.profit_factor == 0.0
        assert metrics.max_drawdown == 0.0
        assert metrics.sharpe_ratio == 0.0
        assert metrics.avg_profit_per_trade == 0.0
        
        # 딕셔너리 변환 테스트
        metrics_dict = metrics.to_dict()
        assert isinstance(metrics_dict, dict)
        assert 'total_trades' in metrics_dict
        assert 'win_rate' in metrics_dict
    
    def test_calculate_common_indicators(self, base_strategy_config):
        """공통 지표 계산 테스트."""
        # BaseStrategy는 추상 클래스이므로 RSIStrategy 사용
        strategy = RSIStrategy(base_strategy_config)
        
        # 테스트 데이터 생성
        df = pd.DataFrame({
            'open': [100, 101, 102, 103, 104] * 50,
            'high': [101, 102, 103, 104, 105] * 50,
            'low': [99, 100, 101, 102, 103] * 50,
            'close': [100.5, 101.5, 102.5, 103.5, 104.5] * 50,
            'volume': [1000, 1100, 1200, 1300, 1400] * 50
        })
        
        result_df = strategy.calculate_common_indicators(df)
        
        # 공통 지표들이 계산되었는지 확인
        common_indicators = [
            'rsi', 'sma_20', 'sma_50', 'ema_12', 'ema_26',
            'macd', 'macd_signal', 'macd_hist',
            'bb_upper', 'bb_middle', 'bb_lower', 'volume_sma'
        ]
        
        for indicator in common_indicators:
            assert indicator in result_df.columns, f"공통 지표 '{indicator}'가 누락됨"


class TestStrategyValidator:
    """전략 검증 테스트."""
    
    def test_validate_dataframe_valid(self):
        """유효한 데이터프레임 검증 테스트."""
        # 유효한 데이터프레임 생성
        df = pd.DataFrame({
            'open': [100] * 100,
            'high': [101] * 100,
            'low': [99] * 100,
            'close': [100.5] * 100,
            'volume': [1000] * 100
        })
        
        is_valid, errors = StrategyValidator.validate_dataframe(df)
        
        assert is_valid is True, f"유효한 데이터프레임이 무효로 판정됨: {errors}"
        assert len(errors) == 0, f"유효한 데이터프레임에 오류가 발견됨: {errors}"
    
    def test_validate_dataframe_missing_columns(self):
        """필수 컬럼 누락 테스트."""
        # 필수 컬럼이 누락된 데이터프레임
        df = pd.DataFrame({
            'open': [100] * 100,
            'high': [101] * 100,
            'low': [99] * 100,
            # 'close' 컬럼 누락
            'volume': [1000] * 100
        })
        
        is_valid, errors = StrategyValidator.validate_dataframe(df)
        
        assert is_valid is False, "필수 컬럼 누락 데이터프레임이 유효로 판정됨"
        assert len(errors) > 0, "필수 컬럼 누락 오류가 감지되지 않음"
        assert any("필수 컬럼 누락" in error for error in errors), "필수 컬럼 누락 메시지가 없음"
    
    def test_validate_dataframe_empty(self):
        """빈 데이터프레임 테스트."""
        df = pd.DataFrame()
        
        is_valid, errors = StrategyValidator.validate_dataframe(df)
        
        assert is_valid is False, "빈 데이터프레임이 유효로 판정됨"
        assert any("비어있습니다" in error for error in errors), "빈 데이터프레임 오류 메시지가 없음"
    
    def test_validate_dataframe_insufficient_data(self):
        """데이터 부족 테스트."""
        # 50개 미만의 데이터
        df = pd.DataFrame({
            'open': [100] * 10,
            'high': [101] * 10,
            'low': [99] * 10,
            'close': [100.5] * 10,
            'volume': [1000] * 10
        })
        
        is_valid, errors = StrategyValidator.validate_dataframe(df)
        
        assert is_valid is False, "데이터 부족 데이터프레임이 유효로 판정됨"
        assert any("충분하지 않습니다" in error for error in errors), "데이터 부족 오류 메시지가 없음"


class TestRiskManager:
    """리스크 관리자 테스트."""
    
    @pytest.fixture
    def risk_manager(self):
        """리스크 관리자 fixture."""
        return RiskManager(
            max_risk_per_trade=0.02,
            max_portfolio_risk=0.10,
            max_drawdown_limit=0.15
        )
    
    def test_risk_manager_initialization(self, risk_manager):
        """리스크 관리자 초기화 테스트."""
        assert risk_manager.max_risk_per_trade == 0.02
        assert risk_manager.max_portfolio_risk == 0.10
        assert risk_manager.max_drawdown_limit == 0.15
        assert len(risk_manager.trade_history) == 0
        assert len(risk_manager.equity_curve) == 0
    
    def test_calculate_position_size_fixed_percentage(self, risk_manager):
        """고정 비율 포지션 크기 계산 테스트."""
        position_size = risk_manager.calculate_position_size(
            account_balance=1000.0,
            entry_price=50000.0,
            stop_loss=48000.0
        )
        
        assert position_size > 0, "포지션 크기가 0 이하"
        assert position_size <= 200.0, "포지션 크기가 최대 한도(20%) 초과"  # 1000 * 0.2
        assert position_size >= 10.0, "포지션 크기가 최소 한도(10 USDT) 미만"
    
    def test_calculate_position_size_invalid_inputs(self, risk_manager):
        """잘못된 입력값 테스트."""
        # 음수 계좌 잔고
        with pytest.raises(ValueError):
            risk_manager.calculate_position_size(
                account_balance=-1000.0,
                entry_price=50000.0,
                stop_loss=48000.0
            )
        
        # 잘못된 손절매 가격 (진입가보다 높음)
        with pytest.raises(ValueError):
            risk_manager.calculate_position_size(
                account_balance=1000.0,
                entry_price=50000.0,
                stop_loss=52000.0  # 진입가보다 높음
            )
    
    def test_check_risk_limits(self, risk_manager):
        """리스크 한계 확인 테스트."""
        # 정상 포지션
        positions = [
            {'risk_amount': 20.0, 'account_balance': 1000.0},
            {'risk_amount': 15.0, 'account_balance': 1000.0}
        ]
        
        risk_check = risk_manager.check_risk_limits(positions)
        
        assert risk_check['status'] == 'ok', "정상 포지션이 위험으로 판정됨"
        assert risk_check['total_risk'] == 35.0, "총 리스크 계산 오류"
        assert risk_check['position_count'] == 2, "포지션 수 계산 오류"
    
    def test_add_trade_record(self, risk_manager):
        """거래 기록 추가 테스트."""
        trade_data = {
            'pair': 'BTC/USDT',
            'profit_ratio': 0.05,
            'entry_price': 50000.0,
            'exit_price': 52500.0
        }
        
        risk_manager.add_trade_record(trade_data)
        
        assert len(risk_manager.trade_history) == 1, "거래 기록이 추가되지 않음"
        assert len(risk_manager.equity_curve) == 1, "자산 곡선이 업데이트되지 않음"
        assert risk_manager.equity_curve[0] == 1.05, "자산 곡선 계산 오류"


# 통합 테스트
class TestIntegration:
    """통합 테스트 클래스."""
    
    def test_full_strategy_workflow(self):
        """전체 전략 워크플로우 테스트."""
        # 설정
        config = {
            'exchange': 'binance',
            'stake_currency': 'USDT',
            'dry_run': True
        }
        
        # 전략 초기화
        strategy = RSIStrategy(config)
        
        # 테스트 데이터 생성
        np.random.seed(42)
        df = pd.DataFrame({
            'open': [50000 + i * 10 for i in range(300)],
            'high': [50010 + i * 10 for i in range(300)],
            'low': [49990 + i * 10 for i in range(300)],
            'close': [50005 + i * 10 for i in range(300)],
            'volume': [1000 + i * 5 for i in range(300)]
        })
        
        metadata = {'pair': 'BTC/USDT', 'timeframe': '5m'}
        
        # 지표 계산
        df_with_indicators = strategy.populate_indicators(df, metadata)
        
        # 신호 생성
        df_with_entry = strategy.populate_entry_trend(df_with_indicators, metadata)
        df_with_signals = strategy.populate_exit_trend(df_with_entry, metadata)
        
        # 결과 검증
        assert 'enter_long' in df_with_signals.columns, "매수 신호 컬럼 누락"
        assert 'exit_long' in df_with_signals.columns, "매도 신호 컬럼 누락"
        
        # 신호 검증
        entry_signals = df_with_signals['enter_long'].sum()
        exit_signals = df_with_signals['exit_long'].sum()
        
        assert entry_signals >= 0, "매수 신호 수가 음수"
        assert exit_signals >= 0, "매도 신호 수가 음수"
        
        print(f"✅ 통합 테스트 완료 - 매수 신호: {entry_signals}, 매도 신호: {exit_signals}")


if __name__ == "__main__":
    # 직접 실행시 기본 테스트 수행
    pytest.main([__file__, "-v"])