"""
MoniGoMani 기반 거래 전략 모듈

MoniGoMani의 가중 신호(Weighted Signals) 개념을 구현한 암호화폐 자동거래 전략입니다.
여러 기술적 지표에 가중치를 부여하고 추세별로 다른 전략을 적용합니다.

Classes:
    MoniGoManiStrategy: 가중 신호 기반 거래 전략 클래스
    
Strategy Logic:
    - 추세 감지: 상승/횡보/하락 추세를 감지
    - 가중 신호: 각 지표에 가중치를 부여하여 종합 점수 계산
    - 적응형 임계값: 시장 상황에 따라 매매 임계값 조정
    
Example:
    from strategies.monigomani_strategy import MoniGoManiStrategy
    
    strategy = MoniGoManiStrategy({})
    dataframe = strategy.populate_indicators(dataframe, metadata)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import talib.abstract as ta
import logging

from core.strategy_base import BaseStrategy

logger = logging.getLogger(__name__)


class MoniGoManiStrategy(BaseStrategy):
    """
    MoniGoMani 기반 가중 신호 거래 전략.
    
    이 전략은 MoniGoMani의 핵심 개념인 가중 신호를 사용하여
    여러 기술적 지표를 조합하고 추세별로 다른 전략을 적용합니다.
    
    Strategy Parameters:
        - 추세 감지: EMA 기반 추세 분류
        - 가중 신호: 8개 주요 지표의 가중 조합
        - 적응형 임계값: 변동성에 따른 임계값 조정
        
    Weighted Signals:
        1. MACD (Moving Average Convergence Divergence)
        2. RSI (Relative Strength Index)
        3. Bollinger Bands
        4. Stochastic
        5. TEMA (Triple Exponential Moving Average)
        6. Volume Weighted Average Price (VWAP)
        7. Money Flow Index (MFI)
        8. Parabolic SAR
        
    Trend Detection:
        - Upward: EMA_fast > EMA_slow and rising
        - Downward: EMA_fast < EMA_slow and falling  
        - Sideways: Other conditions
    """
    
    # 전략 메타데이터
    STRATEGY_NAME = "MoniGoMani_Strategy"
    STRATEGY_VERSION = "1.0.0"
    
    # 시간프레임 설정
    timeframe = '15m'
    startup_candle_count = 300
    
    # ROI 설정 (추세별 차등 적용)
    minimal_roi = {
        "0": 0.15,     # 15% 수익시 즉시 청산
        "30": 0.08,    # 30분 후 8% 수익시 청산
        "60": 0.04,    # 1시간 후 4% 수익시 청산
        "120": 0.02,   # 2시간 후 2% 수익시 청산
        "240": 0.01    # 4시간 후 1% 수익시 청산
    }
    
    # 손절매 설정
    stoploss = -0.05  # 5% 손실시 손절매
    
    # 가중치 파라미터 (추세별로 다른 가중치 적용)
    # 상승 추세 가중치
    upward_weights = {
        'macd': 0.15,
        'rsi': 0.12,
        'bb': 0.10,
        'stoch': 0.08,
        'tema': 0.15,
        'vwap': 0.12,
        'mfi': 0.10,
        'sar': 0.18
    }
    
    # 하락 추세 가중치 (보수적)
    downward_weights = {
        'macd': 0.20,
        'rsi': 0.15,
        'bb': 0.15,
        'stoch': 0.10,
        'tema': 0.10,
        'vwap': 0.10,
        'mfi': 0.08,
        'sar': 0.12
    }
    
    # 횡보 추세 가중치
    sideways_weights = {
        'macd': 0.10,
        'rsi': 0.18,
        'bb': 0.18,
        'stoch': 0.15,
        'tema': 0.08,
        'vwap': 0.10,
        'mfi': 0.12,
        'sar': 0.09
    }
    
    # 신호 임계값
    buy_signal_threshold = 60   # 매수 신호 임계값
    sell_signal_threshold = 40  # 매도 신호 임계값
    
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        MoniGoMani 전략에 필요한 기술적 지표들을 계산합니다.
        
        Args:
            dataframe (pd.DataFrame): OHLCV 데이터
            metadata (dict): 메타데이터 (pair, timeframe 등)
            
        Returns:
            pd.DataFrame: 지표가 추가된 데이터프레임
        """
        try:
            # 기본 지표 계산 (부모 클래스에서)
            dataframe = self.calculate_common_indicators(dataframe)
            
            # 추세 감지를 위한 EMA
            dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=12)
            dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=26)
            dataframe['ema_long'] = ta.EMA(dataframe, timeperiod=50)
            
            # 추세 분류
            dataframe['trend'] = self._classify_trend(dataframe)
            
            # 각 지표별 점수 계산
            dataframe = self._calculate_all_scores(dataframe)
            
            # 가중 신호 계산
            dataframe = self._calculate_weighted_signals(dataframe)
            
            # 변동성 조정
            dataframe['volatility'] = ta.ATR(dataframe, timeperiod=14) / dataframe['close']
            dataframe = self._adjust_for_volatility(dataframe)
            
            # 전체 NaN 처리 (모든 지표에 대해)
            dataframe = dataframe.fillna(method='ffill').fillna(50)
            
            self.log_strategy_info(dataframe, metadata)
            
            return dataframe
            
        except Exception as e:
            logger.error(f"지표 계산 중 오류 발생: {e}")
            return dataframe
    
    def _classify_trend(self, dataframe: pd.DataFrame) -> pd.Series:
        """추세를 분류합니다."""
        try:
            conditions = [
                # 상승 추세: 빠른 EMA가 느린 EMA 위에 있고 상승 중
                (dataframe['ema_fast'] > dataframe['ema_slow']) & 
                (dataframe['ema_fast'] > dataframe['ema_fast'].shift(1)) &
                (dataframe['close'] > dataframe['ema_long']),
                
                # 하락 추세: 빠른 EMA가 느린 EMA 아래에 있고 하락 중
                (dataframe['ema_fast'] < dataframe['ema_slow']) & 
                (dataframe['ema_fast'] < dataframe['ema_fast'].shift(1)) &
                (dataframe['close'] < dataframe['ema_long'])
            ]
            
            choices = ['upward', 'downward']
            
            return pd.Series(
                np.select(conditions, choices, default='sideways'),
                index=dataframe.index
            )
            
        except Exception as e:
            logger.error(f"추세 분류 중 오류: {e}")
            return pd.Series('sideways', index=dataframe.index)
    
    def _calculate_all_scores(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """모든 지표의 점수를 계산합니다."""
        # MACD
        macd_line, macd_signal, macd_hist = ta.MACD(dataframe['close'])
        dataframe['macd'] = macd_line
        dataframe['macd_signal'] = macd_signal
        dataframe['macd_hist'] = macd_hist
        dataframe['macd_score'] = self._calculate_macd_score(dataframe)
        
        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        dataframe['rsi_score'] = self._calculate_rsi_score(dataframe)
        
        # Bollinger Bands
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdev=2)
        dataframe['bb_upper'] = bollinger['upperband']
        dataframe['bb_middle'] = bollinger['middleband']
        dataframe['bb_lower'] = bollinger['lowerband']
        dataframe['bb_score'] = self._calculate_bb_score(dataframe)
        
        # Stochastic
        stoch = ta.STOCH(dataframe)
        dataframe['stoch_k'] = stoch['slowk']
        dataframe['stoch_d'] = stoch['slowd']
        dataframe['stoch_score'] = self._calculate_stoch_score(dataframe)
        
        # TEMA (더 짧은 기간으로 변경하여 NaN 감소)
        dataframe['tema'] = ta.TEMA(dataframe, timeperiod=14)
        dataframe['tema_score'] = self._calculate_tema_score(dataframe)
        
        # VWAP
        typical_price = (dataframe['high'] + dataframe['low'] + dataframe['close']) / 3
        cumulative_volume = dataframe['volume'].cumsum()
        cumulative_pv = (typical_price * dataframe['volume']).cumsum()
        dataframe['vwap'] = cumulative_pv / cumulative_volume
        dataframe['vwap_score'] = self._calculate_vwap_score(dataframe)
        
        # MFI
        dataframe['mfi'] = ta.MFI(dataframe, timeperiod=14)
        dataframe['mfi_score'] = self._calculate_mfi_score(dataframe)
        
        # Parabolic SAR
        dataframe['sar'] = ta.SAR(dataframe)
        dataframe['sar_score'] = self._calculate_sar_score(dataframe)
        
        # NaN 값을 50(중립)으로 대체
        score_columns = [col for col in dataframe.columns if col.endswith('_score')]
        for col in score_columns:
            dataframe[col] = dataframe[col].fillna(50)
        
        return dataframe
    
    def _calculate_macd_score(self, dataframe: pd.DataFrame) -> pd.Series:
        """MACD 신호 점수를 계산합니다."""
        score = pd.Series(50, index=dataframe.index)
        score += np.where(dataframe['macd'] > dataframe['macd_signal'], 20, -20)
        score += np.where(dataframe['macd_hist'] > dataframe['macd_hist'].shift(1), 15, -15)
        score += np.where(dataframe['macd'] > 0, 15, -15)
        return np.clip(score, 0, 100)
    
    def _calculate_rsi_score(self, dataframe: pd.DataFrame) -> pd.Series:
        """RSI 신호 점수를 계산합니다."""
        rsi = dataframe['rsi']
        score = pd.Series(50, index=dataframe.index)
        
        score = np.where(rsi < 30, 80, score)
        score = np.where((rsi >= 30) & (rsi < 40), 70, score)
        score = np.where((rsi >= 40) & (rsi < 60), 50, score)
        score = np.where((rsi >= 60) & (rsi < 70), 30, score)
        score = np.where(rsi >= 70, 20, score)
        
        rsi_trend = rsi - rsi.shift(1)
        score += np.where(rsi_trend > 0, 10, -10)
        
        return np.clip(score, 0, 100)
    
    def _calculate_bb_score(self, dataframe: pd.DataFrame) -> pd.Series:
        """Bollinger Bands 신호 점수를 계산합니다."""
        score = pd.Series(50, index=dataframe.index)
        
        bb_position = (dataframe['close'] - dataframe['bb_lower']) / (
            dataframe['bb_upper'] - dataframe['bb_lower']
        )
        
        score = np.where(bb_position < 0.2, 80, score)
        score = np.where((bb_position >= 0.2) & (bb_position < 0.4), 65, score)
        score = np.where((bb_position >= 0.4) & (bb_position < 0.6), 50, score)
        score = np.where((bb_position >= 0.6) & (bb_position < 0.8), 35, score)
        score = np.where(bb_position >= 0.8, 20, score)
        
        return np.clip(score, 0, 100)
    
    def _calculate_stoch_score(self, dataframe: pd.DataFrame) -> pd.Series:
        """Stochastic 신호 점수를 계산합니다."""
        stoch_k = dataframe['stoch_k']
        stoch_d = dataframe['stoch_d']
        score = pd.Series(50, index=dataframe.index)
        
        score = np.where(stoch_k < 20, 80, score)
        score = np.where((stoch_k >= 20) & (stoch_k < 40), 65, score)
        score = np.where((stoch_k >= 40) & (stoch_k < 60), 50, score)
        score = np.where((stoch_k >= 60) & (stoch_k < 80), 35, score)
        score = np.where(stoch_k >= 80, 20, score)
        
        cross_up = (stoch_k > stoch_d) & (stoch_k.shift(1) <= stoch_d.shift(1))
        cross_down = (stoch_k < stoch_d) & (stoch_k.shift(1) >= stoch_d.shift(1))
        
        score += np.where(cross_up, 15, 0)
        score -= np.where(cross_down, 15, 0)
        
        return np.clip(score, 0, 100)
    
    def _calculate_tema_score(self, dataframe: pd.DataFrame) -> pd.Series:
        """TEMA 신호 점수를 계산합니다."""
        score = pd.Series(50, index=dataframe.index)
        
        # TEMA가 NaN인 경우 중립 점수 유지
        tema_valid = dataframe['tema'].notna()
        
        score += np.where(
            tema_valid & (dataframe['close'] > dataframe['tema']), 25,
            np.where(tema_valid & (dataframe['close'] <= dataframe['tema']), -25, 0)
        )
        
        tema_slope = dataframe['tema'] - dataframe['tema'].shift(1)
        slope_valid = tema_slope.notna()
        
        score += np.where(
            slope_valid & (tema_slope > 0), 25,
            np.where(slope_valid & (tema_slope <= 0), -25, 0)
        )
        
        return np.clip(score, 0, 100)
    
    def _calculate_vwap_score(self, dataframe: pd.DataFrame) -> pd.Series:
        """VWAP 신호 점수를 계산합니다."""
        score = pd.Series(50, index=dataframe.index)
        
        price_vs_vwap = (dataframe['close'] - dataframe['vwap']) / dataframe['vwap']
        
        score += np.where(price_vs_vwap > 0.02, 30, 0)
        score += np.where(price_vs_vwap > 0, 20, -20)
        score += np.where(price_vs_vwap < -0.02, -30, 0)
        
        return np.clip(score, 0, 100)
    
    def _calculate_mfi_score(self, dataframe: pd.DataFrame) -> pd.Series:
        """MFI 신호 점수를 계산합니다."""
        mfi = dataframe['mfi']
        score = pd.Series(50, index=dataframe.index)
        
        score = np.where(mfi < 20, 80, score)
        score = np.where((mfi >= 20) & (mfi < 40), 65, score)
        score = np.where((mfi >= 40) & (mfi < 60), 50, score)
        score = np.where((mfi >= 60) & (mfi < 80), 35, score)
        score = np.where(mfi >= 80, 20, score)
        
        mfi_trend = mfi - mfi.shift(1)
        score += np.where(mfi_trend > 0, 10, -10)
        
        return np.clip(score, 0, 100)
    
    def _calculate_sar_score(self, dataframe: pd.DataFrame) -> pd.Series:
        """Parabolic SAR 신호 점수를 계산합니다."""
        score = pd.Series(50, index=dataframe.index)
        
        score += np.where(dataframe['close'] > dataframe['sar'], 30, -30)
        
        sar_direction_change = (
            (dataframe['close'] > dataframe['sar']) != 
            (dataframe['close'].shift(1) > dataframe['sar'].shift(1))
        )
        
        bullish_reversal = (
            sar_direction_change & 
            (dataframe['close'] > dataframe['sar'])
        )
        
        score += np.where(bullish_reversal, 20, 0)
        
        return np.clip(score, 0, 100)
    
    def _calculate_weighted_signals(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """추세별 가중치를 적용하여 종합 신호를 계산합니다."""
        try:
            for trend in ['upward', 'downward', 'sideways']:
                weights = getattr(self, f'{trend}_weights')
                
                weighted_score = (
                    dataframe['macd_score'] * weights['macd'] +
                    dataframe['rsi_score'] * weights['rsi'] +
                    dataframe['bb_score'] * weights['bb'] +
                    dataframe['stoch_score'] * weights['stoch'] +
                    dataframe['tema_score'] * weights['tema'] +
                    dataframe['vwap_score'] * weights['vwap'] +
                    dataframe['mfi_score'] * weights['mfi'] +
                    dataframe['sar_score'] * weights['sar']
                )
                
                dataframe[f'{trend}_signal'] = weighted_score
            
            # 현재 추세에 따른 최종 신호
            dataframe['final_signal'] = np.select(
                [
                    dataframe['trend'] == 'upward',
                    dataframe['trend'] == 'downward',
                    dataframe['trend'] == 'sideways'
                ],
                [
                    dataframe['upward_signal'],
                    dataframe['downward_signal'],
                    dataframe['sideways_signal']
                ],
                default=50
            )
            
            return dataframe
            
        except Exception as e:
            logger.error(f"가중 신호 계산 중 오류: {e}")
            dataframe['final_signal'] = 50
            return dataframe
    
    def _adjust_for_volatility(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """변동성에 따라 신호를 조정합니다."""
        try:
            vol_percentile = dataframe['volatility'].rolling(50).rank(pct=True)
            vol_adjustment = np.where(vol_percentile > 0.8, 10, 0)
            vol_adjustment += np.where(vol_percentile > 0.9, 5, 0)
            
            dataframe['buy_threshold'] = self.buy_signal_threshold + vol_adjustment
            dataframe['sell_threshold'] = self.sell_signal_threshold - vol_adjustment
            
            return dataframe
            
        except Exception as e:
            logger.error(f"변동성 조정 중 오류: {e}")
            dataframe['buy_threshold'] = self.buy_signal_threshold
            dataframe['sell_threshold'] = self.sell_signal_threshold
            return dataframe
    
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        MoniGoMani 기반 매수 진입 신호를 생성합니다.
        
        매수 조건:
        1. 최종 가중 신호가 매수 임계값 이상
        2. 신호가 상승 추세
        3. 거래량 확인
        4. 추가 필터 조건
        
        Args:
            dataframe (pd.DataFrame): 지표가 계산된 데이터프레임
            metadata (dict): 메타데이터
            
        Returns:
            pd.DataFrame: 'enter_long' 컬럼이 추가된 데이터프레임
        """
        try:
            # 매수 신호 컬럼 초기화
            dataframe['enter_long'] = 0
            
            # 기본 매수 조건
            signal_condition = dataframe['final_signal'] >= dataframe['buy_threshold']
            
            # 신호 상승 추세 확인
            signal_rising = dataframe['final_signal'] > dataframe['final_signal'].shift(1)
            
            # 거래량 조건
            volume_condition = dataframe['volume'] > dataframe['volume'].rolling(20).mean()
            
            # 추세 조건 (하락 추세에서는 더 강한 신호 필요)
            trend_condition = (
                (dataframe['trend'] == 'upward') |
                (dataframe['trend'] == 'sideways') |
                ((dataframe['trend'] == 'downward') & 
                 (dataframe['final_signal'] >= dataframe['buy_threshold'] + 10))
            )
            
            # 추가 확인 조건
            confirmation_condition = (
                (dataframe['rsi'] < 70) &  # 과매수 아님
                (dataframe['close'] > dataframe['ema_fast'])  # 단기 추세 확인
            )
            
            # 최종 매수 신호
            dataframe.loc[
                (
                    signal_condition &
                    signal_rising &
                    volume_condition &
                    trend_condition &
                    confirmation_condition
                ),
                'enter_long'
            ] = 1
            
            # 신호 검증
            self.validate_signal(dataframe, 'enter_long')
            
            return dataframe
            
        except Exception as e:
            logger.error(f"매수 신호 생성 중 오류 발생: {e}")
            dataframe['enter_long'] = 0
            return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        MoniGoMani 기반 매도 청산 신호를 생성합니다.
        
        매도 조건:
        1. 최종 가중 신호가 매도 임계값 이하
        2. 신호가 하락 추세
        3. 추세 변화 감지
        
        Args:
            dataframe (pd.DataFrame): 지표가 계산된 데이터프레임
            metadata (dict): 메타데이터
            
        Returns:
            pd.DataFrame: 'exit_long' 컬럼이 추가된 데이터프레임
        """
        try:
            # 매도 신호 컬럼 초기화
            dataframe['exit_long'] = 0
            
            # 기본 매도 조건
            signal_condition = dataframe['final_signal'] <= dataframe['sell_threshold']
            
            # 신호 하락 추세 확인
            signal_falling = dataframe['final_signal'] < dataframe['final_signal'].shift(1)
            
            # 추세 변화 감지
            trend_change = (
                (dataframe['trend'] == 'downward') |
                ((dataframe['trend'] != 'upward') & 
                 (dataframe['final_signal'] <= dataframe['sell_threshold'] - 5))
            )
            
            # 기술적 매도 신호
            technical_sell = (
                (dataframe['rsi'] > 70) |  # 과매수
                (dataframe['close'] < dataframe['ema_fast'])  # 단기 추세 악화
            )
            
            # 최종 매도 신호
            dataframe.loc[
                (
                    signal_condition &
                    signal_falling &
                    (trend_change | technical_sell)
                ),
                'exit_long'
            ] = 1
            
            # 신호 검증
            self.validate_signal(dataframe, 'exit_long')
            
            return dataframe
            
        except Exception as e:
            logger.error(f"매도 신호 생성 중 오류 발생: {e}")
            dataframe['exit_long'] = 0
            return dataframe


# 전략 테스트 및 검증 함수
def test_monigomani_strategy():
    """MoniGoMani 전략 테스트 함수."""
    try:
        # 테스트용 설정
        config = {
            'exchange': 'binance',
            'stake_currency': 'USDT',
            'dry_run': True
        }
        
        # 전략 인스턴스 생성
        strategy = MoniGoManiStrategy(config)
        
        # 기본 검증
        assert strategy.timeframe == '15m'
        assert strategy.startup_candle_count == 300
        assert strategy.stoploss == -0.05
        
        # 가중치 검증
        for weights in [strategy.upward_weights, strategy.downward_weights, strategy.sideways_weights]:
            total_weight = sum(weights.values())
            assert abs(total_weight - 1.0) < 0.01, f"가중치 합계가 1이 아닙니다: {total_weight}"
        
        print("✅ MoniGoMani 전략 기본 테스트 통과")
        
        # 메트릭 테스트
        metrics = strategy.strategy_metrics
        assert isinstance(metrics.to_dict(), dict)
        
        print("✅ MoniGoMani 전략 모든 테스트 통과")
        
    except Exception as e:
        print(f"❌ MoniGoMani 전략 테스트 실패: {e}")


if __name__ == "__main__":
    test_monigomani_strategy() 