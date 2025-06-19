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
import pandas_ta as pta

class MoniGoManiFreqtrade(IStrategy):
    """
    MoniGoMani 전략 - Freqtrade 버전
    
    다중 지표 가중 신호 기반 전략
    상승/하락/횡보 추세에 따라 다른 가중치 적용
    """

    # Strategy interface version
    INTERFACE_VERSION = 3

    # Optimal timeframe for the strategy
    timeframe = '15m'

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy
    minimal_roi = {
        "0": 0.12,      # 12% 즉시 익절
        "60": 0.08,     # 1시간 후 8%
        "120": 0.04,    # 2시간 후 4%
        "180": 0.02,    # 3시간 후 2%
        "240": 0.01     # 4시간 후 1%
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
    buy_threshold = DecimalParameter(50.0, 70.0, default=55.0, space="buy", optimize=False)
    sell_threshold = DecimalParameter(20.0, 50.0, default=30.0, space="sell", optimize=False)

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        지표들을 계산하고 가중 신호를 생성합니다.
        """

        # MACD
        macd = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe['macd'] = macd['macd']
        dataframe['macdsignal'] = macd['macdsignal']
        dataframe['macdhist'] = macd['macdhist']

        # RSI
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)

        # Bollinger Bands
        bollinger = ta.BBANDS(dataframe, timeperiod=20, nbdev=2)
        dataframe['bb_lowerband'] = bollinger['lowerband']
        dataframe['bb_middleband'] = bollinger['middleband']
        dataframe['bb_upperband'] = bollinger['upperband']
        dataframe['bb_percent'] = (dataframe['close'] - dataframe['bb_lowerband']) / (
            dataframe['bb_upperband'] - dataframe['bb_lowerband']) * 100

        # Stochastic
        stoch = ta.STOCH(dataframe, fastk_period=14, slowk_period=3, slowd_period=3)
        dataframe['slowk'] = stoch['slowk']
        dataframe['slowd'] = stoch['slowd']

        # TEMA
        dataframe['tema'] = ta.TEMA(dataframe, timeperiod=14)

        # VWAP (pandas_ta 사용)
        try:
            dataframe['vwap'] = pta.vwap(dataframe['high'], dataframe['low'], 
                                       dataframe['close'], dataframe['volume'], 
                                       length=14)
        except:
            # VWAP 계산 실패시 SMA로 대체
            dataframe['vwap'] = ta.SMA(dataframe, timeperiod=14)

        # MFI
        dataframe['mfi'] = ta.MFI(dataframe, timeperiod=14)

        # Parabolic SAR
        dataframe['sar'] = ta.SAR(dataframe, acceleration=0.02, maximum=0.2)

        # 추세 분석 (EMA 기반)
        dataframe['ema_short'] = ta.EMA(dataframe, timeperiod=10)
        dataframe['ema_long'] = ta.EMA(dataframe, timeperiod=50)
        
        # 추세 방향 결정
        dataframe['trend'] = np.where(
            dataframe['ema_short'] > dataframe['ema_long'] * 1.02, 'uptrend',
            np.where(dataframe['ema_short'] < dataframe['ema_long'] * 0.98, 'downtrend', 'sideways')
        )

        # 변동성 계산 (ATR 기반)
        dataframe['atr'] = ta.ATR(dataframe, timeperiod=14)
        dataframe['volatility'] = dataframe['atr'] / dataframe['close'] * 100

        # 가중 신호 계산
        dataframe = self.calculate_weighted_signal(dataframe)

        return dataframe

    def calculate_weighted_signal(self, dataframe: DataFrame) -> DataFrame:
        """가중 신호를 계산합니다."""
        
        # 각 지표별 신호 계산 (0-100 스케일)
        signals = pd.DataFrame(index=dataframe.index)
        
        # MACD 신호
        signals['macd_signal'] = np.where(
            dataframe['macd'] > dataframe['macdsignal'], 70, 30
        )
        
        # RSI 신호
        signals['rsi_signal'] = np.where(
            dataframe['rsi'] < 30, 80,
            np.where(dataframe['rsi'] > 70, 20, 50)
        )
        
        # 볼린저밴드 신호
        signals['bb_signal'] = np.where(
            dataframe['bb_percent'] < 20, 75,
            np.where(dataframe['bb_percent'] > 80, 25, 50)
        )
        
        # 스토캐스틱 신호
        signals['stoch_signal'] = np.where(
            (dataframe['slowk'] < 20) & (dataframe['slowd'] < 20), 80,
            np.where((dataframe['slowk'] > 80) & (dataframe['slowd'] > 80), 20, 50)
        )
        
        # TEMA 신호
        signals['tema_signal'] = np.where(
            dataframe['close'] > dataframe['tema'], 65, 35
        )
        
        # VWAP 신호
        signals['vwap_signal'] = np.where(
            dataframe['close'] > dataframe['vwap'], 65, 35
        )
        
        # MFI 신호
        signals['mfi_signal'] = np.where(
            dataframe['mfi'] < 20, 80,
            np.where(dataframe['mfi'] > 80, 20, 50)
        )
        
        # SAR 신호
        signals['sar_signal'] = np.where(
            dataframe['close'] > dataframe['sar'], 70, 30
        )
        
        # 추세별 가중치 적용
        uptrend_weights = {
            'macd_signal': 1.3, 'rsi_signal': 0.8, 'bb_signal': 1.0, 'stoch_signal': 0.9,
            'tema_signal': 1.2, 'vwap_signal': 1.1, 'mfi_signal': 0.9, 'sar_signal': 1.1
        }
        
        downtrend_weights = {
            'macd_signal': 1.1, 'rsi_signal': 1.2, 'bb_signal': 1.1, 'stoch_signal': 1.0,
            'tema_signal': 0.9, 'vwap_signal': 0.8, 'mfi_signal': 1.3, 'sar_signal': 0.9
        }
        
        sideways_weights = {
            'macd_signal': 0.9, 'rsi_signal': 1.3, 'bb_signal': 1.4, 'stoch_signal': 1.2,
            'tema_signal': 0.8, 'vwap_signal': 1.0, 'mfi_signal': 1.1, 'sar_signal': 0.8
        }
        
        # 가중 신호 계산
        weighted_signal = pd.Series(index=dataframe.index, dtype=float)
        
        for i in range(len(dataframe)):
            trend = dataframe['trend'].iloc[i]
            
            if trend == 'uptrend':
                weights = uptrend_weights
            elif trend == 'downtrend':
                weights = downtrend_weights
            else:
                weights = sideways_weights
            
            total_weight = sum(weights.values())
            signal_sum = sum(signals[col].iloc[i] * weights[col] for col in signals.columns)
            weighted_signal.iloc[i] = signal_sum / total_weight
        
        dataframe['weighted_signal'] = weighted_signal.fillna(50)
        
        # 변동성에 따른 임계값 조정
        volatility_adjustment = np.where(
            dataframe['volatility'] > 3.0, 5,  # 고변동성: 임계값 완화
            np.where(dataframe['volatility'] < 1.5, -3, 0)  # 저변동성: 임계값 강화
        )
        
        dataframe['buy_threshold_adj'] = self.buy_threshold.value + volatility_adjustment
        dataframe['sell_threshold_adj'] = self.sell_threshold.value + volatility_adjustment
        
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        매수 신호 생성
        """
        
        dataframe.loc[
            (
                (dataframe['weighted_signal'] >= dataframe['buy_threshold_adj']) &
                (dataframe['volume'] > 0)
            ),
            'enter_long'] = 1

        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        매도 신호 생성
        """
        
        dataframe.loc[
            (
                (dataframe['weighted_signal'] <= dataframe['sell_threshold_adj']) &
                (dataframe['volume'] > 0)
            ),
            'exit_long'] = 1

        return dataframe