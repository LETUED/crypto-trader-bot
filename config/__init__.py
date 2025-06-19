"""
Configuration(설정) 패키지

Freqtrade 암호화폐 자동거래 시스템의 모든 설정을 관리합니다.

Modules:
    settings: 메인 설정 관리 모듈
"""

from .settings import (
    TradingConfig,
    DatabaseConfig, 
    MonitoringConfig,
    ExchangeType,
    TradingMode,
    get_settings,
    get_database_config,
    get_monitoring_config,
    validate_configuration
)

__all__ = [
    "TradingConfig",
    "DatabaseConfig",
    "MonitoringConfig", 
    "ExchangeType",
    "TradingMode",
    "get_settings",
    "get_database_config",
    "get_monitoring_config",
    "validate_configuration"
]