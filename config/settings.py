"""
Freqtrade 암호화폐 자동거래 시스템 설정 모듈

이 모듈은 거래 시스템의 모든 configuration(설정)을 관리합니다.
Pydantic을 사용하여 type validation(타입 검증)과 environment variable(환경변수) 
처리를 제공합니다.

Classes:
    TradingConfig: 메인 거래 시스템 설정
    DatabaseConfig: 데이터베이스 연결 설정
    APIConfig: 외부 API 연결 설정
    
Example:
    from config.settings import get_settings
    
    settings = get_settings()
    print(f"Exchange: {settings.exchange}")
"""

from typing import List, Optional, Dict, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from enum import Enum
import os


class ExchangeType(str, Enum):
    """지원되는 거래소 타입 열거형."""
    BINANCE = "binance"
    UPBIT = "upbit"
    BYBIT = "bybit"
    BITGET = "bitget"


class TradingMode(str, Enum):
    """거래 모드 열거형."""
    DRY_RUN = "dry_run"
    LIVE = "live"
    BACKTEST = "backtest"


class TradingConfig(BaseSettings):
    """
    메인 거래 시스템 설정 클래스.
    
    환경변수 또는 .env 파일에서 설정값을 로드합니다.
    모든 설정값은 validation(검증)을 거칩니다.
    
    Attributes:
        exchange (ExchangeType): 사용할 거래소
        trading_mode (TradingMode): 거래 모드
        api_key (str): 거래소 API 키
        api_secret (str): 거래소 API 시크릿
        max_open_trades (int): 최대 동시 거래 수
        stake_amount (float): 거래당 투자 금액
        
    Raises:
        ValueError: 설정값이 유효하지 않을 때
    """
    
    # 거래소 설정
    exchange: ExchangeType = Field(default=ExchangeType.BINANCE, description="사용할 거래소")
    trading_mode: TradingMode = Field(default=TradingMode.DRY_RUN, description="거래 모드")
    
    # API 인증 정보 (드라이런 모드에서는 선택적)
    api_key: str = Field(default="dummy_key", description="거래소 API 키")
    api_secret: str = Field(default="dummy_secret", description="거래소 API 시크릿")
    sandbox_mode: bool = Field(default=True, description="샌드박스 모드 사용 여부")
    
    # 거래 설정
    max_open_trades: int = Field(default=3, description="최대 동시 거래 수")
    stake_amount: float = Field(default=100.0, description="거래당 투자 금액 (USDT)")
    stake_currency: str = Field(default="USDT", description="기준 통화")
    
    # 리스크 관리
    max_risk_per_trade: float = Field(default=0.02, description="거래당 최대 리스크 (2%)")
    stop_loss_percentage: float = Field(default=0.05, description="손절매 비율 (5%)")
    take_profit_percentage: float = Field(default=0.10, description="익절 비율 (10%)")
    
    # 거래 쌍 설정
    trading_pairs: List[str] = Field(
        default=["BTC/USDT", "ETH/USDT", "BNB/USDT"],
        description="거래할 암호화폐 쌍"
    )
    
    # 시간 설정
    timeframe: str = Field(default="5m", description="기본 시간프레임")
    startup_candle_count: int = Field(default=200, description="시작시 로드할 캔들 수")
    
    @field_validator('max_risk_per_trade')
    @classmethod
    def validate_risk_percentage(cls, v):
        """리스크 비율 검증 - 0.1%에서 10% 사이여야 함."""
        if not 0.001 <= v <= 0.1:
            raise ValueError('리스크 비율은 0.1%에서 10% 사이여야 합니다')
        return v
    
    @field_validator('max_open_trades')
    @classmethod
    def validate_max_trades(cls, v):
        """최대 거래 수 검증 - 1에서 20 사이여야 함."""
        if not 1 <= v <= 20:
            raise ValueError('최대 거래 수는 1에서 20 사이여야 합니다')
        return v
    
    @field_validator('stake_amount')
    @classmethod
    def validate_stake_amount(cls, v):
        """투자 금액 검증 - 최소 10 USDT."""
        if v < 10:
            raise ValueError('투자 금액은 최소 10 USDT 이상이어야 합니다')
        return v
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "FREQTRADE_",
        "case_sensitive": False,
        "extra": "ignore"
    }


class DatabaseConfig(BaseSettings):
    """
    데이터베이스 연결 설정.
    
    SQLite 또는 PostgreSQL 데이터베이스 연결을 관리합니다.
    """
    
    db_url: str = Field(
        default="sqlite:///data/tradesv3.sqlite",
        description="데이터베이스 연결 URL"
    )
    echo_sql: bool = Field(default=False, description="SQL 쿼리 로깅 여부")
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "DB_",
        "extra": "ignore"
    }


class MonitoringConfig(BaseSettings):
    """
    모니터링 및 알림 설정.
    
    텔레그램 봇, 웹훅 등의 알림 설정을 관리합니다.
    """
    
    # 텔레그램 설정
    telegram_enabled: bool = Field(default=False, description="텔레그램 알림 사용 여부")
    telegram_token: Optional[str] = Field(default=None, description="텔레그램 봇 토큰")
    telegram_chat_id: Optional[str] = Field(default=None, description="텔레그램 채팅 ID")
    
    # 웹 인터페이스 설정
    api_server_enabled: bool = Field(default=True, description="API 서버 사용 여부")
    api_server_host: str = Field(default="127.0.0.1", description="API 서버 호스트")
    api_server_port: int = Field(default=8080, description="API 서버 포트")
    
    # 로깅 설정
    log_level: str = Field(default="INFO", description="로그 레벨")
    log_file: str = Field(default="logs/freqtrade.log", description="로그 파일 경로")
    
    model_config = {
        "env_file": ".env",
        "env_prefix": "MONITOR_",
        "extra": "ignore"
    }


def get_settings() -> TradingConfig:
    """
    싱글톤 패턴으로 설정 인스턴스를 반환합니다.
    
    Returns:
        TradingConfig: 거래 시스템 설정 인스턴스
        
    Example:
        >>> settings = get_settings()
        >>> print(settings.exchange)
        ExchangeType.BINANCE
    """
    return TradingConfig()


def get_database_config() -> DatabaseConfig:
    """데이터베이스 설정 인스턴스를 반환합니다."""
    return DatabaseConfig()


def get_monitoring_config() -> MonitoringConfig:
    """모니터링 설정 인스턴스를 반환합니다."""
    return MonitoringConfig()


# 설정 검증 함수
def validate_configuration() -> Dict[str, Any]:
    """
    전체 시스템 설정을 검증하고 상태를 반환합니다.
    
    Returns:
        Dict[str, Any]: 설정 검증 결과
        
    Raises:
        ValueError: 필수 설정이 누락되었거나 잘못된 경우
    """
    try:
        trading_config = get_settings()
        db_config = get_database_config()
        monitor_config = get_monitoring_config()
        
        validation_result = {
            "status": "valid",
            "trading_mode": trading_config.trading_mode,
            "exchange": trading_config.exchange,
            "max_trades": trading_config.max_open_trades,
            "database_configured": bool(db_config.db_url),
            "monitoring_enabled": monitor_config.telegram_enabled or monitor_config.api_server_enabled
        }
        
        return validation_result
        
    except Exception as e:
        return {
            "status": "invalid",
            "error": str(e)
        }


if __name__ == "__main__":
    # 설정 테스트
    print("=== Freqtrade 설정 검증 ===")
    result = validate_configuration()
    print(f"검증 결과: {result}")