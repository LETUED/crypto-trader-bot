"""
로깅 시스템 모듈

Freqtrade 암호화폐 자동거래 시스템을 위한 구조화된 로깅 시스템입니다.
structlog를 사용하여 JSON 형태의 구조화된 로그를 생성합니다.

Classes:
    LoggerSetup: 로거 설정 관리 클래스
    TradingLogger: 거래 전용 로거 클래스
    
Functions:
    setup_logging(): 로깅 시스템 초기화
    get_logger(): 로거 인스턴스 반환
    
Example:
    from utils.logger import setup_logging, get_logger
    
    setup_logging()
    logger = get_logger(__name__)
    logger.info("거래 시작", pair="BTC/USDT", action="BUY")
"""

import logging
import structlog
import sys
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import json
from config.settings import get_monitoring_config


def setup_logging(
    log_level: str = "INFO",
    log_file: Optional[str] = None,
    enable_json_logs: bool = True
) -> None:
    """
    구조화된 로깅 시스템을 설정합니다.
    
    Args:
        log_level (str): 로그 레벨 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file (str, optional): 로그 파일 경로
        enable_json_logs (bool): JSON 형태 로그 활성화 여부
    """
    try:
        # 로그 디렉토리 생성
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 기본 로깅 설정
        logging.basicConfig(
            format="%(message)s",
            stream=sys.stdout,
            level=getattr(logging, log_level.upper())
        )
        
        # structlog 프로세서 설정
        processors = [
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
        ]
        
        if enable_json_logs:
            processors.append(structlog.processors.JSONRenderer())
        else:
            processors.append(structlog.dev.ConsoleRenderer())
        
        structlog.configure(
            processors=processors,
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # 파일 핸들러 추가
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(getattr(logging, log_level.upper()))
            
            if enable_json_logs:
                file_formatter = logging.Formatter('%(message)s')
            else:
                file_formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            
            file_handler.setFormatter(file_formatter)
            logging.getLogger().addHandler(file_handler)
        
        logger = get_logger(__name__)
        logger.info("로깅 시스템 초기화 완료", log_level=log_level, log_file=log_file)
        
    except Exception as e:
        print(f"로깅 설정 실패: {e}")
        # 기본 로깅으로 폴백
        logging.basicConfig(level=logging.INFO)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    구조화된 로거 인스턴스를 반환합니다.
    
    Args:
        name (str): 로거 이름 (보통 __name__ 사용)
        
    Returns:
        structlog.BoundLogger: 구조화된 로거 인스턴스
    """
    return structlog.get_logger(name)


class TradingLogger:
    """
    거래 전용 로거 클래스.
    
    거래 관련 이벤트들을 구조화된 형태로 로깅합니다.
    """
    
    def __init__(self, logger_name: str = "trading"):
        """
        거래 로거 초기화.
        
        Args:
            logger_name (str): 로거 이름
        """
        self.logger = get_logger(logger_name)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def log_strategy_signal(
        self,
        pair: str,
        signal_type: str,
        strategy_name: str,
        price: float,
        indicators: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        전략 신호 로깅.
        
        Args:
            pair (str): 거래 쌍
            signal_type (str): 신호 타입 (BUY, SELL)
            strategy_name (str): 전략 이름
            price (float): 현재 가격
            indicators (Dict, optional): 기술적 지표 값들
        """
        self.logger.info(
            "전략 신호 생성",
            event_type="strategy_signal",
            session_id=self.session_id,
            pair=pair,
            signal_type=signal_type,
            strategy_name=strategy_name,
            price=price,
            indicators=indicators or {}
        )
    
    def log_trade_entry(
        self,
        pair: str,
        side: str,
        amount: float,
        price: float,
        order_id: str,
        strategy_name: str
    ) -> None:
        """
        거래 진입 로깅.
        
        Args:
            pair (str): 거래 쌍
            side (str): 매수/매도 (BUY/SELL)
            amount (float): 거래량
            price (float): 진입 가격
            order_id (str): 주문 ID
            strategy_name (str): 전략 이름
        """
        self.logger.info(
            "거래 진입",
            event_type="trade_entry",
            session_id=self.session_id,
            pair=pair,
            side=side,
            amount=amount,
            price=price,
            order_id=order_id,
            strategy_name=strategy_name
        )
    
    def log_trade_exit(
        self,
        pair: str,
        side: str,
        amount: float,
        entry_price: float,
        exit_price: float,
        profit_loss: float,
        profit_percentage: float,
        order_id: str,
        exit_reason: str
    ) -> None:
        """
        거래 청산 로깅.
        
        Args:
            pair (str): 거래 쌍
            side (str): 매수/매도
            amount (float): 거래량
            entry_price (float): 진입 가격
            exit_price (float): 청산 가격
            profit_loss (float): 손익 금액
            profit_percentage (float): 손익 비율
            order_id (str): 주문 ID
            exit_reason (str): 청산 이유
        """
        self.logger.info(
            "거래 청산",
            event_type="trade_exit",
            session_id=self.session_id,
            pair=pair,
            side=side,
            amount=amount,
            entry_price=entry_price,
            exit_price=exit_price,
            profit_loss=profit_loss,
            profit_percentage=profit_percentage,
            order_id=order_id,
            exit_reason=exit_reason
        )
    
    def log_risk_event(
        self,
        event_type: str,
        description: str,
        risk_level: str,
        current_drawdown: Optional[float] = None,
        portfolio_risk: Optional[float] = None
    ) -> None:
        """
        리스크 관련 이벤트 로깅.
        
        Args:
            event_type (str): 이벤트 타입
            description (str): 설명
            risk_level (str): 리스크 레벨 (LOW, MEDIUM, HIGH, CRITICAL)
            current_drawdown (float, optional): 현재 손실폭
            portfolio_risk (float, optional): 포트폴리오 리스크
        """
        self.logger.warning(
            "리���크 이벤트",
            event_type="risk_event",
            session_id=self.session_id,
            risk_event_type=event_type,
            description=description,
            risk_level=risk_level,
            current_drawdown=current_drawdown,
            portfolio_risk=portfolio_risk
        )
    
    def log_system_event(
        self,
        event_type: str,
        description: str,
        level: str = "INFO",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        시스템 이벤트 로깅.
        
        Args:
            event_type (str): 이벤트 타입
            description (str): 설명
            level (str): 로그 레벨
            additional_data (Dict, optional): 추가 데이터
        """
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        
        log_method(
            description,
            event_type="system_event",
            session_id=self.session_id,
            system_event_type=event_type,
            additional_data=additional_data or {}
        )
    
    def log_performance_metrics(
        self,
        metrics: Dict[str, Any],
        period: str = "daily"
    ) -> None:
        """
        성능 지표 로깅.
        
        Args:
            metrics (Dict[str, Any]): 성능 지표
            period (str): 기간 (daily, weekly, monthly)
        """
        self.logger.info(
            "성능 지표 업데이트",
            event_type="performance_metrics",
            session_id=self.session_id,
            period=period,
            metrics=metrics
        )


class LogAnalyzer:
    """로그 분석 유틸리티 클래스."""
    
    def __init__(self, log_file_path: str):
        """
        로그 분석기 초기화.
        
        Args:
            log_file_path (str): 분석할 로그 파일 경로
        """
        self.log_file_path = log_file_path
    
    def parse_trading_logs(self, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        거래 로그를 파싱하여 분석 데이터를 반환합니다.
        
        Args:
            start_date (datetime, optional): 시작 날짜
            end_date (datetime, optional): 종료 날짜
            
        Returns:
            Dict[str, Any]: 파싱된 거래 데이터
        """
        try:
            trades = []
            signals = []
            risk_events = []
            
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())
                        event_type = log_entry.get('event_type')
                        
                        # 날짜 필터링
                        log_timestamp = datetime.fromisoformat(log_entry.get('timestamp', '').replace('Z', '+00:00'))
                        
                        if start_date and log_timestamp < start_date:
                            continue
                        if end_date and log_timestamp > end_date:
                            continue
                        
                        # 이벤트 타입별 분류
                        if event_type == 'trade_entry' or event_type == 'trade_exit':
                            trades.append(log_entry)
                        elif event_type == 'strategy_signal':
                            signals.append(log_entry)
                        elif event_type == 'risk_event':
                            risk_events.append(log_entry)
                            
                    except json.JSONDecodeError:
                        continue  # 잘못된 JSON 라인 스킵
            
            return {
                'trades': trades,
                'signals': signals,
                'risk_events': risk_events,
                'summary': {
                    'total_trades': len(trades),
                    'total_signals': len(signals),
                    'total_risk_events': len(risk_events)
                }
            }
            
        except Exception as e:
            logger = get_logger(__name__)
            logger.error("로그 파싱 중 오류 발생", error=str(e))
            return {}
    
    def generate_trading_report(self, parsed_logs: Dict[str, Any]) -> str:
        """
        파싱된 로그를 바탕으로 거래 리포트를 생성합니다.
        
        Args:
            parsed_logs (Dict[str, Any]): 파싱된 로그 데이터
            
        Returns:
            str: 거래 리포트 텍스트
        """
        try:
            trades = parsed_logs.get('trades', [])
            signals = parsed_logs.get('signals', [])
            risk_events = parsed_logs.get('risk_events', [])
            
            # 기본 통계
            entry_trades = [t for t in trades if t.get('event_type') == 'trade_entry']
            exit_trades = [t for t in trades if t.get('event_type') == 'trade_exit']
            
            # 수익성 분석
            profitable_trades = [t for t in exit_trades if t.get('profit_loss', 0) > 0]
            losing_trades = [t for t in exit_trades if t.get('profit_loss', 0) < 0]
            
            win_rate = len(profitable_trades) / len(exit_trades) if exit_trades else 0
            total_profit = sum(t.get('profit_loss', 0) for t in exit_trades)
            
            report = f"""
=== 거래 시스템 리포트 ===

📊 기본 통계:
- 총 거래 진입: {len(entry_trades)}회
- 총 거래 청산: {len(exit_trades)}회
- 총 신호 생성: {len(signals)}회
- 리스크 이벤트: {len(risk_events)}회

💰 수익성 분석:
- 승률: {win_rate:.2%}
- 수익 거래: {len(profitable_trades)}회
- 손실 거래: {len(losing_trades)}회
- 총 손익: {total_profit:.2f} USDT

⚠️ 리스크 이벤트:
"""
            
            # 리스크 이벤트 상세
            for risk_event in risk_events[-5:]:  # 최근 5개
                report += f"- {risk_event.get('description', 'N/A')} (레벨: {risk_event.get('risk_level', 'N/A')})\n"
            
            return report
            
        except Exception as e:
            return f"리포트 생성 실패: {e}"


# 초기화 함수
def initialize_logging():
    """설정 파일을 바탕으로 로깅 시스템을 초기화합니다."""
    try:
        monitor_config = get_monitoring_config()
        setup_logging(
            log_level=monitor_config.log_level,
            log_file=monitor_config.log_file,
            enable_json_logs=True
        )
    except Exception as e:
        print(f"로깅 초기화 실패, 기본 설정 사용: {e}")
        setup_logging()


if __name__ == "__main__":
    # 테스트 코드
    initialize_logging()
    
    # 테스트 로거
    trading_logger = TradingLogger()
    
    # 테스트 로그 생성
    trading_logger.log_strategy_signal(
        pair="BTC/USDT",
        signal_type="BUY",
        strategy_name="RSIStrategy",
        price=50000.0,
        indicators={"rsi": 25.5, "macd": 0.002}
    )
    
    trading_logger.log_trade_entry(
        pair="BTC/USDT",
        side="BUY",
        amount=0.001,
        price=50000.0,
        order_id="12345",
        strategy_name="RSIStrategy"
    )
    
    print("✅ 로깅 시스템 테스트 완료")