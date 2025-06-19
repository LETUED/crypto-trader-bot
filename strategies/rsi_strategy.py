"""
RSI 기반 거래 전략 모듈

RSI(Relative Strength Index) 지표를 활용한 암호화폐 자동거래 전략입니다.
과매수/과매도 구간에서의 역추세 매매를 기본으로 합니다.

Classes:
    RSIStrategy: RSI 기반 거래 전략 클래스
    
Strategy Logic:
    - 매수: RSI < 30 (과매도) + 볼린저밴드 하단 터치
    - 매도: RSI > 70 (과매수) + 볼린저밴드 상단 터치
    - 추가 필터: 거래량 증가, MACD 확인
    
Example:
    from strategies.rsi_strategy import RSIStrategy
    
    strategy = RSIStrategy({})
    dataframe = strategy.populate_indicators(dataframe, metadata)
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import talib.abstract as ta
import logging

from core.strategy_base import BaseStrategy

logger = logging.getLogger(__name__)


class RSIStrategy(BaseStrategy):
    """
    RSI(Relative Strength Index) 기반 거래 전략.
    
    이 전략은 RSI 지표를 주요 신호로 사용하며, 추가적인 확인 지표들로
    신호의 신뢰성을 높입니다.
    
    Strategy Parameters:
        - RSI 기간: 14
        - 과매도 기준: 30
        - 과매수 기준: 70
        - 볼린저밴드 기간: 20
        - 볼린저밴드 표준편차: 2
        
    Entry Conditions (매수):
        1. RSI < 30 (과매도)
        2. 가격이 볼린저밴드 하단 근처
        3. 거래량이 평균보다 높음
        4. MACD 히스토그램이 상승 전환
        
    Exit Conditions (매도):
        1. RSI > 70 (과매수)
        2. 가격이 볼린저밴드 상단 근처
        3. MACD 히스토그램이 하락 전환
    """
    
    # 전략 메타데이터
    STRATEGY_NAME = "RSI_Strategy"
    STRATEGY_VERSION = "1.0.0"
    
    # 시간프레임 설정
    timeframe = '5m'
    startup_candle_count = 200
    
    # ROI 설정 (더 보수적으로 조정)
    minimal_roi = {
        "0": 0.08,     # 8% 수익시 즉시 청산
        "15": 0.04,    # 15분 후 4% 수익시 청산
        "30": 0.02,    # 30분 후 2% 수익시 청산
        "60": 0.01     # 1시간 후 1% 수익시 청산
    }
    
    # 손절매 설정
    stoploss = -0.04  # 4% 손실시 손절매
    
    # 전략 파라미터
    rsi_period = 14
    rsi_oversold = 30
    rsi_overbought = 70
    bb_period = 20
    bb_std = 2
    volume_lookback = 20
    
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        RSI 전략에 필요한 기술적 지표들을 계산합니다.
        
        Args:
            dataframe (pd.DataFrame): OHLCV 데이터
            metadata (dict): 메타데이터 (pair, timeframe 등)
            
        Returns:
            pd.DataFrame: 지표가 추가된 데이터프레임
        """
        try:
            # 기본 지표 계산 (부모 클래스에서)
            dataframe = self.calculate_common_indicators(dataframe)
            
            # RSI 계산 (추가 기간별)
            dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period)
            dataframe['rsi_slow'] = ta.RSI(dataframe, timeperiod=21)  # 느린 RSI
            
            # 볼린저 밴드 (추가 설정)
            bollinger = ta.BBANDS(dataframe, timeperiod=self.bb_period, nbdev=self.bb_std)
            dataframe['bb_upper'] = bollinger['upperband']
            dataframe['bb_middle'] = bollinger['middleband']
            dataframe['bb_lower'] = bollinger['lowerband']
            dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle']
            dataframe['bb_position'] = (dataframe['close'] - dataframe['bb_lower']) / (dataframe['bb_upper'] - dataframe['bb_lower'])
            
            # 거래량 지표
            dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=self.volume_lookback)
            dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']
            
            # MACD 상세 분석
            macd_line, macd_signal, macd_hist = ta.MACD(dataframe['close'])
            dataframe['macd'] = macd_line
            dataframe['macd_signal'] = macd_signal
            dataframe['macd_hist'] = macd_hist
            dataframe['macd_hist_shift'] = dataframe['macd_hist'].shift(1)
            
            # 추세 확인을 위한 이동평균
            dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=12)
            dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=26)
            dataframe['trend'] = np.where(dataframe['ema_fast'] > dataframe['ema_slow'], 1, -1)
            
            # 가격 모멘텀
            dataframe['price_change'] = dataframe['close'].pct_change()
            dataframe['price_momentum'] = ta.ROC(dataframe, timeperiod=10)
            
            # 변동성 지표
            dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
            dataframe['volatility'] = dataframe['atr'] / dataframe['close']
            
            self.log_strategy_info(dataframe, metadata)
            
            return dataframe
            
        except Exception as e:
            logger.error(f"지표 계산 중 오류 발생: {e}")
            return dataframe
    
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        RSI 기반 매수 진입 신호를 생성합니다.
        
        매수 조건:
        1. RSI가 과매도 구간 (30 이하)
        2. 가격이 볼린저밴드 하단 20% 이내
        3. 거래량이 평균의 1.2배 이상
        4. MACD 히스토그램이 상승 전환 (음수에서 양수로)
        5. 전체적인 추세가 하락이 아님
        
        Args:
            dataframe (pd.DataFrame): 지표가 계산된 데이터프레임
            metadata (dict): 메타데이터
            
        Returns:
            pd.DataFrame: 'enter_long' 컬럼이 추가된 데이터프레임
        """
        try:
            # 기본 매수 조건
            condition_rsi_oversold = dataframe['rsi'] <= self.rsi_oversold
            condition_rsi_rising = dataframe['rsi'] > dataframe['rsi'].shift(1)
            
            # 볼린저밴드 조건
            condition_bb_low = dataframe['bb_position'] <= 0.2  # 하단 20% 이내
            condition_bb_squeeze = dataframe['bb_width'] > dataframe['bb_width'].rolling(20).mean()
            
            # 거래량 조건
            condition_volume = dataframe['volume_ratio'] >= 1.2
            
            # MACD 조건 (상승 전환)
            condition_macd_bullish = (
                (dataframe['macd_hist'] > 0) & 
                (dataframe['macd_hist_shift'] <= 0)
            ) | (
                (dataframe['macd_hist'] > dataframe['macd_hist_shift']) & 
                (dataframe['macd_hist'] < 0) & 
                (dataframe['macd_hist'] > -0.001)  # 0에 가까워짐
            )
            
            # 추세 조건 (강한 하락추세가 아님)
            condition_trend = dataframe['trend'] >= 0  # 상승 또는 횡보
            
            # 변동성 조건 (너무 높은 변동성 제외)
            condition_volatility = dataframe['volatility'] <= dataframe['volatility'].rolling(50).quantile(0.8)
            
            # 최종 매수 신호
            dataframe.loc[
                (
                    condition_rsi_oversold &
                    condition_rsi_rising &
                    condition_bb_low &
                    condition_volume &
                    condition_macd_bullish &
                    condition_trend &
                    condition_volatility
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
        RSI 기반 매도 청산 신호를 생성합니다.
        
        매도 조건:
        1. RSI가 과매수 구간 (70 이상)
        2. 가격이 볼린저밴드 상단 80% 이상
        3. MACD 히스토그램이 하락 전환
        4. RSI 다이버전스 감지
        
        Args:
            dataframe (pd.DataFrame): 지표가 계산된 데이터프레임
            metadata (dict): 메타데이터
            
        Returns:
            pd.DataFrame: 'exit_long' 컬럼이 추가된 데이터프레임
        """
        try:
            # 기본 매도 조건
            condition_rsi_overbought = dataframe['rsi'] >= self.rsi_overbought
            condition_rsi_falling = dataframe['rsi'] < dataframe['rsi'].shift(1)
            
            # 볼린저밴드 조건
            condition_bb_high = dataframe['bb_position'] >= 0.8  # 상단 80% 이상
            
            # MACD 조건 (하락 전환)
            condition_macd_bearish = (
                (dataframe['macd_hist'] < 0) & 
                (dataframe['macd_hist_shift'] >= 0)
            ) | (
                (dataframe['macd_hist'] < dataframe['macd_hist_shift']) & 
                (dataframe['macd_hist'] > 0)
            )
            
            # RSI 다이버전스 (간단한 버전)
            # 가격은 상승하지만 RSI는 하락하는 경우
            price_higher = dataframe['close'] > dataframe['close'].shift(5)
            rsi_lower = dataframe['rsi'] < dataframe['rsi'].shift(5)
            condition_divergence = price_higher & rsi_lower & (dataframe['rsi'] > 60)
            
            # 수익 보호 조건 (추가적인 안전장치)
            condition_profit_protect = dataframe['close'] > dataframe['ema_fast']
            
            # 최종 매도 신호
            dataframe.loc[
                (
                    (
                        condition_rsi_overbought &
                        condition_rsi_falling &
                        condition_bb_high &
                        condition_macd_bearish
                    ) |
                    condition_divergence
                ) &
                condition_profit_protect,
                'exit_long'
            ] = 1
            
            # 신호 검증
            self.validate_signal(dataframe, 'exit_long')
            
            return dataframe
            
        except Exception as e:
            logger.error(f"매도 신호 생성 중 오류 발생: {e}")
            dataframe['exit_long'] = 0
            return dataframe
    
    def custom_sell(self, pair: str, trade, current_time, current_rate, current_profit, **kwargs) -> bool:
        """
        커스텀 매도 로직.
        
        특정 조건에서 강제 매도를 실행합니다.
        
        Args:
            pair (str): 거래 쌍
            trade: 현재 거래 정보
            current_time: 현재 시간
            current_rate (float): 현재 가격
            current_profit (float): 현재 수익률
            
        Returns:
            bool: 매도 실행 여부
        """
        try:
            # 손실이 3% 이상이고 거래 시간이 2시간 이상인 경우
            if current_profit <= -0.03 and (current_time - trade.open_date_utc).seconds >= 7200:
                logger.info(f"시간 기반 손절매 실행: {pair}, 수익률: {current_profit:.2%}")
                return True
            
            # 수익이 15% 이상인 경우 부분 매도 고려
            if current_profit >= 0.15:
                logger.info(f"고수익 구간 매도 고려: {pair}, 수익률: {current_profit:.2%}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"커스텀 매도 로직 오류: {e}")
            return False
    
    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, **kwargs) -> bool:
        """
        거래 진입 전 최종 확인.
        
        Args:
            pair (str): 거래 쌍
            order_type (str): 주문 타입
            amount (float): 거래량
            rate (float): 거래 가격
            
        Returns:
            bool: 거래 진입 승인 여부
        """
        try:
            # 시장 상황 확인 (예: 급격한 변동성 체크)
            # 실제 구현에서는 더 정교한 로직 필요
            
            logger.info(
                f"거래 진입 확인 - Pair: {pair}, "
                f"Type: {order_type}, Amount: {amount:.4f}, Rate: {rate:.4f}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"거래 진입 확인 중 오류: {e}")
            return False


# 전략 테스트 및 검증 함수
def test_rsi_strategy():
    """RSI 전략 테스트 함수."""
    try:
        # 테스트용 설정
        config = {
            'exchange': 'binance',
            'stake_currency': 'USDT',
            'dry_run': True
        }
        
        # 전략 인스턴스 생성
        strategy = RSIStrategy(config)
        
        # 기본 검증
        assert strategy.timeframe == '5m'
        assert strategy.startup_candle_count == 200
        assert strategy.stoploss == -0.04
        
        print("✅ RSI 전략 기본 테스트 통과")
        
        # 메트릭 테스트
        metrics = strategy.strategy_metrics
        assert isinstance(metrics.to_dict(), dict)
        
        print("✅ RSI 전략 모든 테스트 통과")
        
    except Exception as e:
        print(f"❌ RSI 전략 테스트 실패: {e}")


if __name__ == "__main__":
    test_rsi_strategy()