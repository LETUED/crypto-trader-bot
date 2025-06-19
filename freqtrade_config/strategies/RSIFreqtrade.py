# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these libs ---
import numpy as np
import pandas as pd
from pandas import DataFrame
from datetime import datetime
from typing import Optional, Union

from freqtrade.strategy import (BooleanParameter, CategoricalParameter, DecimalParameter,
                                IntParameter, IStrategy, merge_informative_pair)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta

class RSIFreqtrade(IStrategy):
    """
    RSI 전략 - Freqtrade 버전
    
    RSI 과매수/과매도 기반 역추세 매매 전략
    볼린저밴드, MACD, 거래량 필터 추가
    """

    # Strategy interface version
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy
    timeframe = '5m'

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy
    minimal_roi = {
        "0": 0.08,     # 8% 수익시 즉시 청산
        "15": 0.04,    # 15분 후 4% 수익시 청산
        "30": 0.02,    # 30분 후 2% 수익시 청산
        "60": 0.01     # 1시간 후 1% 수익시 청산
    }

    # Optimal stoploss designed for the strategy
    stoploss = -0.04

    # Trailing stoploss
    trailing_stop = False

    # Run "populate_indicators()" only for new candle
    process_only_new_candles = False

    # These values can be overridden in the config
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 200

    # Strategy parameters
    rsi_period = IntParameter(10, 20, default=14, space="buy", optimize=False)
    rsi_oversold = IntParameter(25, 35, default=30, space="buy", optimize=False)
    rsi_overbought = IntParameter(65, 75, default=70, space="sell", optimize=False)
    
    bb_period = IntParameter(15, 25, default=20, space="buy", optimize=False)
    bb_std = DecimalParameter(1.5, 2.5, default=2.0, space="buy", optimize=False)
    
    volume_lookback = IntParameter(15, 25, default=20, space="buy", optimize=False)

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        RSI 전략에 필요한 기술적 지표들을 계산합니다.
        """

        # RSI 계산
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=self.rsi_period.value)
        dataframe['rsi_slow'] = ta.RSI(dataframe, timeperiod=21)

        # 볼린저 밴드
        bollinger = ta.BBANDS(dataframe, timeperiod=self.bb_period.value, nbdev=self.bb_std.value)
        dataframe['bb_upper'] = bollinger['upperband']
        dataframe['bb_middle'] = bollinger['middleband']
        dataframe['bb_lower'] = bollinger['lowerband']
        dataframe['bb_width'] = (dataframe['bb_upper'] - dataframe['bb_lower']) / dataframe['bb_middle']
        dataframe['bb_position'] = (dataframe['close'] - dataframe['bb_lower']) / (dataframe['bb_upper'] - dataframe['bb_lower'])

        # 거래량 지표
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=self.volume_lookback.value)
        dataframe['volume_ratio'] = dataframe['volume'] / dataframe['volume_sma']

        # MACD
        macd_line, macd_signal, macd_hist = ta.MACD(dataframe['close'])
        dataframe['macd'] = macd_line
        dataframe['macd_signal'] = macd_signal
        dataframe['macd_hist'] = macd_hist
        dataframe['macd_hist_shift'] = dataframe['macd_hist'].shift(1)

        # 추세 확인을 위한 이동평균
        dataframe['ema_fast'] = ta.EMA(dataframe, timeperiod=12)
        dataframe['ema_slow'] = ta.EMA(dataframe, timeperiod=26)
        dataframe['trend'] = np.where(dataframe['ema_fast'] > dataframe['ema_slow'], 1, -1)

        # 변동성 지표
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['volatility'] = dataframe['atr'] / dataframe['close']

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        RSI 기반 매수 진입 신호를 생성합니다.
        
        매수 조건:
        1. RSI가 과매도 구간 (30 이하)
        2. RSI가 상승 중
        3. 가격이 볼린저밴드 하단 20% 이내
        4. 거래량이 평균의 1.2배 이상
        5. MACD 히스토그램이 상승 전환
        6. 전체적인 추세가 하락이 아님
        """
        
        dataframe.loc[
            (
                # RSI 조건
                (dataframe['rsi'] <= self.rsi_oversold.value) &
                (dataframe['rsi'] > dataframe['rsi'].shift(1)) &
                
                # 볼린저밴드 조건
                (dataframe['bb_position'] <= 0.2) &
                
                # 거래량 조건
                (dataframe['volume_ratio'] >= 1.2) &
                
                # MACD 조건 (상승 전환)
                (
                    ((dataframe['macd_hist'] > 0) & (dataframe['macd_hist_shift'] <= 0)) |
                    ((dataframe['macd_hist'] > dataframe['macd_hist_shift']) & 
                     (dataframe['macd_hist'] < 0) & 
                     (dataframe['macd_hist'] > -0.001))
                ) &
                
                # 추세 조건
                (dataframe['trend'] >= 0) &
                
                # 변동성 조건
                (dataframe['volatility'] <= dataframe['volatility'].rolling(50).quantile(0.8)) &
                
                # 기본 조건
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        RSI 기반 매도 신호를 생성합니다.
        
        매도 조건:
        1. RSI가 과매수 구간 (70 이상)
        2. 가격이 볼린저밴드 상단 80% 이상
        3. MACD 히스토그램이 하락 전환
        """
        
        dataframe.loc[
            (
                # RSI 조건
                (dataframe['rsi'] >= self.rsi_overbought.value) &
                
                # 볼린저밴드 조건
                (dataframe['bb_position'] >= 0.8) &
                
                # MACD 조건 (하락 전환)
                (
                    ((dataframe['macd_hist'] < 0) & (dataframe['macd_hist_shift'] >= 0)) |
                    ((dataframe['macd_hist'] < dataframe['macd_hist_shift']) & 
                     (dataframe['macd_hist'] > 0))
                ) &
                
                # 기본 조건
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1

        return dataframe