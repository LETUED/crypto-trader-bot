"""
거래 전략 기본 클래스 모듈

이 모듈은 모든 거래 strategy(전략)의 기반이 되는 abstract base class(추상 기본 클래스)를 
제공합니다. Freqtrade IStrategy를 확장하여 추가적인 기능을 제공합니다.

Classes:
    BaseStrategy: 모든 거래 전략의 기본 클래스
    StrategyMetrics: 전략 성능 지표 클래스
    
Example:
    from core.strategy_base import BaseStrategy
    
    class MyStrategy(BaseStrategy):
        def populate_indicators(self, dataframe, metadata):
            # 지표 계산 로직
            return dataframe
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter
import talib.abstract as ta
import logging

# 로거 설정
logger = logging.getLogger(__name__)


@dataclass
class StrategyMetrics:
    """
    전략 성능 지표를 저장하는 데이터 클래스.
    
    Attributes:
        total_trades (int): 총 거래 수
        win_rate (float): 승률 (0.0 ~ 1.0)
        profit_factor (float): 수익 팩터
        max_drawdown (float): 최대 손실폭
        sharpe_ratio (float): 샤프 비율
        avg_profit_per_trade (float): 거래당 평균 수익률
    """
    
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    avg_profit_per_trade: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """메트릭을 딕셔너리로 변환합니다."""
        return {
            'total_trades': self.total_trades,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'avg_profit_per_trade': self.avg_profit_per_trade
        }


class BaseStrategy(IStrategy, ABC):
    """
    모든 거래 전략의 기본 클래스.
    
    Freqtrade의 IStrategy를 상속하여 공통 기능을 제공합니다.
    모든 사용자 정의 전략은 이 클래스를 상속해야 합니다.
    
    Attributes:
        INTERFACE_VERSION (int): Freqtrade 인터페이스 버전
        timeframe (str): 기본 시간프레임
        startup_candle_count (int): 시작시 필요한 캔들 수
        minimal_roi (dict): 최소 ROI 설정
        stoploss (float): 기본 손절매 비율
        
    Methods:
        populate_indicators(): 지표 계산 (추상 메서드)
        populate_entry_trend(): 진입 신호 생성 (추상 메서드)
        populate_exit_trend(): 청산 신호 생성 (추상 메서드)
        calculate_metrics(): 전략 성능 지표 계산
    """
    
    # Freqtrade 필수 설정
    INTERFACE_VERSION: int = 3
    
    # 기본 전략 설정
    timeframe = '5m'
    startup_candle_count: int = 200
    
    # ROI 설정 (시간대별 최소 수익률)
    minimal_roi = {
        "0": 0.1,      # 10% 수익시 즉시 청산
        "30": 0.05,    # 30분 후 5% 수익시 청산
        "60": 0.02,    # 1시간 후 2% 수익시 청산
        "120": 0.01    # 2시간 후 1% 수익시 청산
    }
    
    # 손절매 설정
    stoploss = -0.05  # 5% 손실시 손절매
    
    # 매개변수 최적화를 위한 파라미터
    buy_rsi_threshold = IntParameter(20, 40, default=30, space="buy")
    sell_rsi_threshold = IntParameter(60, 80, default=70, space="sell")
    
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        전략 초기화.
        
        Args:
            config (Dict[str, Any]): Freqtrade 설정 딕셔너리
        """
        super().__init__(config)
        self.strategy_metrics = StrategyMetrics()
        logger.info(f"전략 초기화 완료: {self.__class__.__name__}")
    
    @abstractmethod
    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        기술적 지표를 계산합니다.
        
        모든 하위 클래스에서 반드시 구현해야 하는 추상 메서드입니다.
        
        Args:
            dataframe (pd.DataFrame): OHLCV 데이터
            metadata (dict): 메타데이터 (pair, timeframe 등)
            
        Returns:
            pd.DataFrame: 지표가 추가된 데이터프레임
            
        Example:
            def populate_indicators(self, dataframe, metadata):
                dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
                dataframe['sma_20'] = ta.SMA(dataframe, timeperiod=20)
                return dataframe
        """
        pass
    
    @abstractmethod
    def populate_entry_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        매수 진입 신호를 생성합니다.
        
        Args:
            dataframe (pd.DataFrame): 지표가 계산된 데이터프레임
            metadata (dict): 메타데이터
            
        Returns:
            pd.DataFrame: 'enter_long' 컬럼이 추가된 데이터프레임
        """
        pass
    
    @abstractmethod
    def populate_exit_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        """
        매도 청산 신호를 생성합니다.
        
        Args:
            dataframe (pd.DataFrame): 지표가 계산된 데이터프레임
            metadata (dict): 메타데이터
            
        Returns:
            pd.DataFrame: 'exit_long' 컬럼이 추가된 데이터프레임
        """
        pass
    
    def calculate_common_indicators(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """
        공통으로 사용되는 기술적 지표들을 계산합니다.
        
        Args:
            dataframe (pd.DataFrame): OHLCV 데이터
            
        Returns:
            pd.DataFrame: 공통 지표가 추가된 데이터프레임
        """
        # RSI (Relative Strength Index)
        dataframe['rsi'] = ta.RSI(dataframe, timeperiod=14)
        
        # 이동평균선
        dataframe['sma_20'] = ta.SMA(dataframe, timeperiod=20)
        dataframe['sma_50'] = ta.SMA(dataframe, timeperiod=50)
        dataframe['ema_12'] = ta.EMA(dataframe, timeperiod=12)
        dataframe['ema_26'] = ta.EMA(dataframe, timeperiod=26)
        
        # MACD
        macd = ta.MACD(dataframe)
        dataframe['macd'] = macd['macd']
        dataframe['macd_signal'] = macd['macdsignal']
        dataframe['macd_hist'] = macd['macdhist']
        
        # 볼린저 밴드
        bollinger = ta.BBANDS(dataframe, timeperiod=20)
        dataframe['bb_upper'] = bollinger['upperband']
        dataframe['bb_middle'] = bollinger['middleband']
        dataframe['bb_lower'] = bollinger['lowerband']
        
        # 거래량 지표
        dataframe['volume_sma'] = ta.SMA(dataframe['volume'], timeperiod=20)
        
        return dataframe
    
    def validate_signal(self, dataframe: pd.DataFrame, signal_type: str) -> bool:
        """
        생성된 신호의 유효성을 검증합니다.
        
        Args:
            dataframe (pd.DataFrame): 신호가 포함된 데이터프레임
            signal_type (str): 신호 타입 ('enter_long' 또는 'exit_long')
            
        Returns:
            bool: 신호가 유효한지 여부
        """
        try:
            if signal_type not in dataframe.columns:
                logger.warning(f"신호 컬럼 '{signal_type}'이 데이터프레임에 없습니다")
                return False
            
            signal_count = dataframe[signal_type].sum()
            total_candles = len(dataframe)
            signal_ratio = signal_count / total_candles if total_candles > 0 else 0
            
            # 신호 비율이 너무 높거나 낮으면 경고
            if signal_ratio > 0.5:
                logger.warning(f"신호 비율이 너무 높습니다: {signal_ratio:.2%}")
            elif signal_ratio < 0.01:
                logger.warning(f"신호 비율이 너무 낮습니다: {signal_ratio:.2%}")
            
            return True
            
        except Exception as e:
            logger.error(f"신호 검증 중 오류 발생: {e}")
            return False
    
    def calculate_metrics(self, trades_df: pd.DataFrame) -> StrategyMetrics:
        """
        전략의 성능 지표를 계산합니다.
        
        Args:
            trades_df (pd.DataFrame): 거래 내역 데이터프레임
            
        Returns:
            StrategyMetrics: 계산된 성능 지표
        """
        try:
            if trades_df.empty:
                return StrategyMetrics()
            
            # 기본 지표 계산
            total_trades = len(trades_df)
            winning_trades = len(trades_df[trades_df['profit_ratio'] > 0])
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # 수익 관련 지표
            total_profit = trades_df['profit_ratio'].sum()
            avg_profit_per_trade = total_profit / total_trades if total_trades > 0 else 0
            
            # 손익 팩터 계산
            gross_profit = trades_df[trades_df['profit_ratio'] > 0]['profit_ratio'].sum()
            gross_loss = abs(trades_df[trades_df['profit_ratio'] < 0]['profit_ratio'].sum())
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
            
            # 최대 손실폭 계산 (간단한 버전)
            cumulative_returns = trades_df['profit_ratio'].cumsum()
            max_drawdown = (cumulative_returns.cummax() - cumulative_returns).max()
            
            # 샤프 비율 계산 (간단한 버전)
            returns_std = trades_df['profit_ratio'].std()
            sharpe_ratio = avg_profit_per_trade / returns_std if returns_std > 0 else 0
            
            self.strategy_metrics = StrategyMetrics(
                total_trades=total_trades,
                win_rate=win_rate,
                profit_factor=profit_factor,
                max_drawdown=max_drawdown,
                sharpe_ratio=sharpe_ratio,
                avg_profit_per_trade=avg_profit_per_trade
            )
            
            return self.strategy_metrics
            
        except Exception as e:
            logger.error(f"성능 지표 계산 중 오류 발생: {e}")
            return StrategyMetrics()
    
    def log_strategy_info(self, dataframe: pd.DataFrame, metadata: dict) -> None:
        """
        전략 실행 정보를 로깅합니다.
        
        Args:
            dataframe (pd.DataFrame): 현재 데이터프레임
            metadata (dict): 메타데이터
        """
        pair = metadata.get('pair', 'Unknown')
        latest_close = dataframe['close'].iloc[-1] if not dataframe.empty else 0
        
        logger.info(
            f"전략 실행 - Pair: {pair}, "
            f"Latest Price: {latest_close:.4f}, "
            f"Candles: {len(dataframe)}"
        )


class StrategyValidator:
    """전략 검증을 위한 유틸리티 클래스."""
    
    @staticmethod
    def validate_dataframe(dataframe: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        데이터프레임의 유효성을 검증합니다.
        
        Args:
            dataframe (pd.DataFrame): 검증할 데이터프레임
            
        Returns:
            Tuple[bool, List[str]]: (유효성 여부, 오류 메시지 리스트)
        """
        errors = []
        
        # 필수 컬럼 확인
        required_columns = ['open', 'high', 'low', 'close', 'volume']
        missing_columns = [col for col in required_columns if col not in dataframe.columns]
        if missing_columns:
            errors.append(f"필수 컬럼 누락: {missing_columns}")
        
        # 데이터 유효성 확인
        if dataframe.empty:
            errors.append("데이터프레임이 비어있습니다")
        elif len(dataframe) < 50:
            errors.append("데이터가 충분하지 않습니다 (최소 50개 캔들 필요)")
        
        # NaN 값 확인
        if dataframe.isnull().any().any():
            errors.append("데이터에 NaN 값이 포함되어 있습니다")
        
        return len(errors) == 0, errors