"""
Core(핵심) 모듈 패키지

Freqtrade 암호화폐 자동거래 시스템의 핵심 기능을 제공합니다.

Modules:
    strategy_base: 거래 전략 기본 클래스
    risk_manager: 리스크 관리 모듈
    data_processor: 데이터 처리 모듈
"""

from .strategy_base import BaseStrategy, StrategyMetrics, StrategyValidator

__all__ = [
    "BaseStrategy",
    "StrategyMetrics", 
    "StrategyValidator"
]