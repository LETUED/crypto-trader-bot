#!/usr/bin/env python3
"""
최적화된 MoniGoMani 전략

백테스팅을 통해 최적화된 파라미터를 사용하는 MoniGoMani 전략입니다.
- 매수 임계값: 55 (기존 60에서 하향)
- 매도 임계값: 30 (기존 40에서 하향)
- 더 공격적인 거래로 높은 수익률 추구
"""

import talib as ta
import numpy as np
import pandas as pd
from typing import Dict, Optional
from core.strategy_base import BaseStrategy

class OptimizedMoniGoManiStrategy(BaseStrategy):
    """최적화된 MoniGoMani 전략 클래스"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        
        # 최적화된 파라미터 설정
        self.buy_signal_threshold = 55.0  # 최적화: 60 → 55
        self.sell_signal_threshold = 30.0  # 최적화: 40 → 30
        
        # 지표 설정 (기존 유지)
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.rsi_period = 14
        self.bb_period = 20
        self.bb_std = 2
        self.stoch_k = 14
        self.stoch_d = 3
        self.tema_period = 14  # 21에서 14로 단축
        self.mfi_period = 14
        self.sar_acceleration = 0.02
        self.sar_maximum = 0.2
        
        # 추세별 가중치 (최적화된 값)
        self.uptrend_weights = {
            'macd': 0.20,
            'rsi': 0.15,
            'bb': 0.12,
            'stoch': 0.10,
            'tema': 0.15,
            'vwap': 0.08,
            'mfi': 0.10,
            'sar': 0.10
        }
        
        self.downtrend_weights = {
            'macd': 0.15,
            'rsi': 0.20,
            'bb': 0.15,
            'stoch': 0.12,
            'tema': 0.10,
            'vwap': 0.08,
            'mfi': 0.12,
            'sar': 0.08
        }
        
        self.sideways_weights = {
            'macd': 0.10,
            'rsi': 0.18,
            'bb': 0.20,
            'stoch': 0.15,
            'tema': 0.12,
            'vwap': 0.10,
            'mfi': 0.08,
            'sar': 0.07
        }
        
        # ROI 설정 (더 공격적으로 수정)
        self.minimal_roi = {
            "0": 0.12,    # 12% (기존 15%에서 하향)
            "15": 0.08,   # 8% (기존 8% 유지)
            "30": 0.05,   # 5% (기존 4%에서 상향)
            "60": 0.03,   # 3% (기존 2%에서 상향)
            "120": 0.01   # 1% (기존 1% 유지)
        }
        
        # 손절매 (조금 더 보수적으로)
        self.stoploss = -0.04  # -4% (기존 -5%에서 상향)
        
        # 시간프레임
        self.timeframe = '15m'
    
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """지표를 계산합니다."""
        try:
            df = dataframe.copy()
            
            # MACD 지표
            macd_line, macd_signal, macd_histogram = ta.MACD(
                df['close'].values,
                fastperiod=self.macd_fast,
                slowperiod=self.macd_slow,
                signalperiod=self.macd_signal
            )
            df['macd'] = macd_line
            df['macd_signal'] = macd_signal
            df['macd_histogram'] = macd_histogram
            
            # RSI 지표
            df['rsi'] = ta.RSI(df['close'].values, timeperiod=self.rsi_period)
            
            # 볼린저 밴드
            bb_upper, bb_middle, bb_lower = ta.BBANDS(
                df['close'].values,
                timeperiod=self.bb_period,
                nbdevup=self.bb_std,
                nbdevdn=self.bb_std
            )
            df['bb_upper'] = bb_upper
            df['bb_middle'] = bb_middle
            df['bb_lower'] = bb_lower
            
            # 스토캐스틱
            stoch_k, stoch_d = ta.STOCH(
                df['high'].values,
                df['low'].values,
                df['close'].values,
                fastk_period=self.stoch_k,
                slowk_period=self.stoch_d,
                slowd_period=self.stoch_d
            )
            df['stoch_k'] = stoch_k
            df['stoch_d'] = stoch_d
            
            # TEMA (Triple Exponential Moving Average)
            df['tema'] = ta.TEMA(df['close'].values, timeperiod=self.tema_period)
            
            # VWAP (Volume Weighted Average Price)
            df['vwap'] = (df['close'] * df['volume']).cumsum() / df['volume'].cumsum()
            
            # MFI (Money Flow Index)
            df['mfi'] = ta.MFI(
                df['high'].values,
                df['low'].values,
                df['close'].values,
                df['volume'].values,
                timeperiod=self.mfi_period
            )
            
            # Parabolic SAR
            df['sar'] = ta.SAR(
                df['high'].values,
                df['low'].values,
                acceleration=self.sar_acceleration,
                maximum=self.sar_maximum
            )
            
            # 추세 판단
            df['trend'] = self._determine_trend(df)
            
            # 개별 지표 신호 계산
            df = self._calculate_individual_signals(df)
            
            # 가중 신호 계산
            df = self._calculate_weighted_signals(df)
            
            # NaN 값 처리
            df = df.fillna(method='ffill').fillna(50)
            
            return df
            
        except Exception as e:
            print(f"지표 계산 오류: {e}")
            return dataframe
    
    def _determine_trend(self, df: pd.DataFrame) -> pd.Series:
        """시장 추세를 판단합니다."""
        try:
            # EMA를 이용한 추세 판단
            ema_short = ta.EMA(df['close'].values, timeperiod=10)
            ema_long = ta.EMA(df['close'].values, timeperiod=30)
            
            conditions = [
                (ema_short > ema_long * 1.01),  # 상승 추세 (1% 이상 차이)
                (ema_short < ema_long * 0.99),  # 하락 추세 (1% 이상 차이)
            ]
            
            choices = ['uptrend', 'downtrend']
            
            trend = pd.Series(
                np.select(conditions, choices, default='sideways'),
                index=df.index
            )
            
            return trend
            
        except Exception as e:
            print(f"추세 판단 오류: {e}")
            return pd.Series(['sideways'] * len(df), index=df.index)
    
    def _calculate_individual_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """개별 지표의 신호를 계산합니다."""
        try:
            # MACD 신호 (0-100 스케일)
            df['macd_signal_score'] = np.where(
                (df['macd'] > df['macd_signal']) & (df['macd_histogram'] > 0),
                70 + np.clip(df['macd_histogram'] * 1000, 0, 30),  # 매수 신호
                np.where(
                    (df['macd'] < df['macd_signal']) & (df['macd_histogram'] < 0),
                    30 - np.clip(abs(df['macd_histogram']) * 1000, 0, 30),  # 매도 신호
                    50  # 중립
                )
            )
            
            # RSI 신호
            df['rsi_signal_score'] = np.where(
                df['rsi'] < 35,  # 과매도 (더 관대하게)
                75 + (35 - df['rsi']) * 0.8,
                np.where(
                    df['rsi'] > 65,  # 과매수 (더 관대하게)
                    25 - (df['rsi'] - 65) * 0.8,
                    50  # 중립
                )
            )
            
            # 볼린저 밴드 신호
            bb_position = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
            df['bb_signal_score'] = np.where(
                bb_position < 0.2,  # 하단 근처
                80 - bb_position * 100,
                np.where(
                    bb_position > 0.8,  # 상단 근처
                    20 + (1 - bb_position) * 100,
                    50  # 중립
                )
            )
            
            # 스토캐스틱 신호
            df['stoch_signal_score'] = np.where(
                (df['stoch_k'] < 25) & (df['stoch_d'] < 25),  # 과매도
                75 + (25 - df['stoch_k']) * 0.5,
                np.where(
                    (df['stoch_k'] > 75) & (df['stoch_d'] > 75),  # 과매수
                    25 - (df['stoch_k'] - 75) * 0.5,
                    50  # 중립
                )
            )
            
            # TEMA 신호
            df['tema_signal_score'] = np.where(
                df['close'] > df['tema'] * 1.005,  # 0.5% 이상
                65 + np.clip((df['close'] / df['tema'] - 1) * 2000, 0, 25),
                np.where(
                    df['close'] < df['tema'] * 0.995,  # 0.5% 이하
                    35 - np.clip((1 - df['close'] / df['tema']) * 2000, 0, 25),
                    50  # 중립
                )
            )
            
            # VWAP 신호
            df['vwap_signal_score'] = np.where(
                df['close'] > df['vwap'] * 1.002,  # 0.2% 이상
                60 + np.clip((df['close'] / df['vwap'] - 1) * 3000, 0, 30),
                np.where(
                    df['close'] < df['vwap'] * 0.998,  # 0.2% 이하
                    40 - np.clip((1 - df['close'] / df['vwap']) * 3000, 0, 30),
                    50  # 중립
                )
            )
            
            # MFI 신호
            df['mfi_signal_score'] = np.where(
                df['mfi'] < 25,  # 과매도
                75 + (25 - df['mfi']) * 0.8,
                np.where(
                    df['mfi'] > 75,  # 과매수
                    25 - (df['mfi'] - 75) * 0.8,
                    50  # 중립
                )
            )
            
            # Parabolic SAR 신호
            df['sar_signal_score'] = np.where(
                df['close'] > df['sar'],  # 상승 추세
                65,
                35  # 하락 추세
            )
            
            return df
            
        except Exception as e:
            print(f"개별 신호 계산 오류: {e}")
            # 오류 시 중립 신호 반환
            signal_cols = ['macd_signal_score', 'rsi_signal_score', 'bb_signal_score',
                          'stoch_signal_score', 'tema_signal_score', 'vwap_signal_score',
                          'mfi_signal_score', 'sar_signal_score']
            for col in signal_cols:
                df[col] = 50
            return df
    
    def _calculate_weighted_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """추세별 가중치를 적용하여 최종 신호를 계산합니다."""
        try:
            # 각 추세별로 가중 신호 계산
            uptrend_mask = df['trend'] == 'uptrend'
            downtrend_mask = df['trend'] == 'downtrend'
            sideways_mask = df['trend'] == 'sideways'
            
            df['weighted_signal'] = 50.0  # 기본값
            
            # 상승 추세
            if uptrend_mask.any():
                uptrend_signal = (
                    df.loc[uptrend_mask, 'macd_signal_score'] * self.uptrend_weights['macd'] +
                    df.loc[uptrend_mask, 'rsi_signal_score'] * self.uptrend_weights['rsi'] +
                    df.loc[uptrend_mask, 'bb_signal_score'] * self.uptrend_weights['bb'] +
                    df.loc[uptrend_mask, 'stoch_signal_score'] * self.uptrend_weights['stoch'] +
                    df.loc[uptrend_mask, 'tema_signal_score'] * self.uptrend_weights['tema'] +
                    df.loc[uptrend_mask, 'vwap_signal_score'] * self.uptrend_weights['vwap'] +
                    df.loc[uptrend_mask, 'mfi_signal_score'] * self.uptrend_weights['mfi'] +
                    df.loc[uptrend_mask, 'sar_signal_score'] * self.uptrend_weights['sar']
                )
                df.loc[uptrend_mask, 'weighted_signal'] = uptrend_signal
            
            # 하락 추세
            if downtrend_mask.any():
                downtrend_signal = (
                    df.loc[downtrend_mask, 'macd_signal_score'] * self.downtrend_weights['macd'] +
                    df.loc[downtrend_mask, 'rsi_signal_score'] * self.downtrend_weights['rsi'] +
                    df.loc[downtrend_mask, 'bb_signal_score'] * self.downtrend_weights['bb'] +
                    df.loc[downtrend_mask, 'stoch_signal_score'] * self.downtrend_weights['stoch'] +
                    df.loc[downtrend_mask, 'tema_signal_score'] * self.downtrend_weights['tema'] +
                    df.loc[downtrend_mask, 'vwap_signal_score'] * self.downtrend_weights['vwap'] +
                    df.loc[downtrend_mask, 'mfi_signal_score'] * self.downtrend_weights['mfi'] +
                    df.loc[downtrend_mask, 'sar_signal_score'] * self.downtrend_weights['sar']
                )
                df.loc[downtrend_mask, 'weighted_signal'] = downtrend_signal
            
            # 횡보 추세
            if sideways_mask.any():
                sideways_signal = (
                    df.loc[sideways_mask, 'macd_signal_score'] * self.sideways_weights['macd'] +
                    df.loc[sideways_mask, 'rsi_signal_score'] * self.sideways_weights['rsi'] +
                    df.loc[sideways_mask, 'bb_signal_score'] * self.sideways_weights['bb'] +
                    df.loc[sideways_mask, 'stoch_signal_score'] * self.sideways_weights['stoch'] +
                    df.loc[sideways_mask, 'tema_signal_score'] * self.sideways_weights['tema'] +
                    df.loc[sideways_mask, 'vwap_signal_score'] * self.sideways_weights['vwap'] +
                    df.loc[sideways_mask, 'mfi_signal_score'] * self.sideways_weights['mfi'] +
                    df.loc[sideways_mask, 'sar_signal_score'] * self.sideways_weights['sar']
                )
                df.loc[sideways_mask, 'weighted_signal'] = sideways_signal
            
            # 신호 범위 제한 (0-100)
            df['weighted_signal'] = np.clip(df['weighted_signal'], 0, 100)
            
            return df
            
        except Exception as e:
            print(f"가중 신호 계산 오류: {e}")
            df['weighted_signal'] = 50.0
            return df
    
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """매수 신호를 생성합니다."""
        try:
            df = dataframe.copy()
            
            # 최적화된 임계값 사용 (55)
            buy_conditions = (
                (df['weighted_signal'] > self.buy_signal_threshold) &
                (df['volume'] > df['volume'].rolling(20).mean())  # 거래량 확인
            )
            
            df['enter_long'] = buy_conditions.astype(int)
            
            # 디버깅 정보
            buy_signals = df['enter_long'].sum()
            total_candles = len(df)
            buy_signal_ratio = (buy_signals / total_candles) * 100
            
            print(f"매수 신호: {buy_signals}개 ({buy_signal_ratio:.2f}%)")
            
            return df
            
        except Exception as e:
            print(f"매수 신호 생성 오류: {e}")
            dataframe['enter_long'] = 0
            return dataframe
    
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """매도 신호를 생성합니다."""
        try:
            df = dataframe.copy()
            
            # 최적화된 임계값 사용 (30)
            sell_conditions = (
                df['weighted_signal'] < self.sell_signal_threshold
            )
            
            df['exit_long'] = sell_conditions.astype(int)
            
            # 디버깅 정보
            sell_signals = df['exit_long'].sum()
            total_candles = len(df)
            sell_signal_ratio = (sell_signals / total_candles) * 100
            
            print(f"매도 신호: {sell_signals}개 ({sell_signal_ratio:.2f}%)")
            
            return df
            
        except Exception as e:
            print(f"매도 신호 생성 오류: {e}")
            dataframe['exit_long'] = 0
            return dataframe 