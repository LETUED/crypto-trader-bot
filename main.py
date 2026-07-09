#!/usr/bin/env python3
"""
Freqtrade 암호화폐 자동거래 시스템 메인 실행 파일

이 파일은 전체 거래 시스템의 진입점입니다.
설정 검증, 로깅 초기화, 전략 로드 및 Freqtrade 실행을 관리합니다.

Usage:
    python main.py --config config.json --strategy RSIStrategy
    python main.py --dry-run --strategy RSIStrategy
    python main.py --backtest --timerange 20231201-20240201
    
Commands:
    run: 실시간 거래 실행
    backtest: 백테스트 실행
    plot: 백테스트 결과 차트 생성
    validate: 설정 및 전략 검증
    
Example:
    # 드라이런 모드로 실행
    python main.py run --dry-run --strategy RSIStrategy
    
    # 백테스트 실행
    python main.py backtest --strategy RSIStrategy --timerange 20231201-20240201
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import json
from datetime import datetime, timedelta

# 프로젝트 루트를 Python path에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 로컬 imports
from config import (
    get_settings, 
    get_database_config, 
    get_monitoring_config,
    validate_configuration,
    TradingMode
)
from utils.logger import initialize_logging, get_logger, TradingLogger
from strategies import RSIStrategy
from core.risk_manager import RiskManager
import subprocess


def create_freqtrade_config(
    trading_config,
    db_config, 
    monitor_config,
    strategy_name: str = "RSIStrategy"
) -> Dict[str, Any]:
    """
    Freqtrade 설정 파일을 생성합니다.
    
    Args:
        trading_config: 거래 설정
        db_config: 데이터베이스 설정
        monitor_config: 모니터링 설정
        strategy_name (str): 사용할 전략 이름
        
    Returns:
        Dict[str, Any]: Freqtrade 설정 딕셔너리
    """
    try:
        config = {
            # 기본 설정
            "max_open_trades": trading_config.max_open_trades,
            "stake_currency": trading_config.stake_currency,
            "stake_amount": trading_config.stake_amount,
            "tradable_balance_ratio": 0.99,
            "fiat_display_currency": "USD",
            "dry_run": trading_config.trading_mode == TradingMode.DRY_RUN,
            "cancel_open_orders_on_exit": True,
            
            # 거래소 설정
            "exchange": {
                "name": trading_config.exchange.value,
                "key": trading_config.api_key,
                "secret": trading_config.api_secret,
                "sandbox": trading_config.sandbox_mode,
                "ccxt_config": {
                    "enableRateLimit": True,
                    "rateLimit": 200
                },
                "ccxt_async_config": {
                    "enableRateLimit": True,
                    "rateLimit": 200
                },
                "pair_whitelist": trading_config.trading_pairs,
                "pair_blacklist": [
                    "BNB/BTC", "BNB/BUSD", "BNB/ETH", "BNB/EUR", "BNB/NGN", 
                    "BNB/PAX", "BNB/RUB", "BNB/TRY", "BNB/TUSD", "BNB/USDC",
                    "BNB/USDT", "BNB/VAI"
                ]
            },
            
            # 전략 설정
            "strategy": strategy_name,
            "strategy_path": "user_data/strategies/",
            
            # 데이터베이스 설정
            "db_url": db_config.db_url,
            
            # 로깅 설정
            "logfile": monitor_config.log_file,
            "verbosity": 3,
            
            # API 서버 설정
            "api_server": {
                "enabled": monitor_config.api_server_enabled,
                "listen_ip_address": monitor_config.api_server_host,
                "listen_port": monitor_config.api_server_port,
                "verbosity": "info",
                "enable_openapi": True,
                "jwt_secret_key": "CHANGE_ME",
                "CORS_origins": ["http://localhost:3000"],
                "username": "admin",
                "password": "CHANGE_ME"
            },
            
            # 텔레그램 설정
            "telegram": {
                "enabled": monitor_config.telegram_enabled,
                "token": monitor_config.telegram_token or "",
                "chat_id": monitor_config.telegram_chat_id or "",
                "notification_settings": {
                    "status": "on",
                    "warning": "on", 
                    "startup": "on",
                    "entry": "on",
                    "entry_fill": "on",
                    "exit": "on",
                    "exit_fill": "on",
                    "protection_trigger": "on",
                    "protection_trigger_global": "on"
                }
            },
            
            # 백테스트 설정
            "datadir": "user_data/data",
            "timeframe": trading_config.timeframe,
            "startup_candle_count": trading_config.startup_candle_count,
            
            # 리스크 관리
            "amount_reserve_percent": 0.05,  # 5% 여유금 유지
            "max_open_trades": trading_config.max_open_trades,
            
            # 주문 설정
            "order_types": {
                "entry": "limit",
                "exit": "limit",
                "emergency_exit": "market",
                "force_exit": "market",
                "force_entry": "market",
                "stoploss": "market",
                "stoploss_on_exchange": False,
                "stoploss_on_exchange_interval": 60
            },
            
            "entry_pricing": {
                "price_side": "same",
                "use_order_book": True,
                "order_book_top": 1,
                "price_last_balance": 0.0,
                "check_depth_of_market": {
                    "enabled": False,
                    "bids_to_ask_delta": 1
                }
            },
            
            "exit_pricing": {
                "price_side": "same",
                "use_order_book": True,
                "order_book_top": 1
            },
            
            # 페어리스트 설정
            "pairlists": [
                {
                    "method": "StaticPairList"
                }
            ],
            
            # 보호 설정은 별도 파일로 관리 (deprecated 설정 제거)
        }
        
        return config
        
    except Exception as e:
        logger = get_logger(__name__)
        logger.error("Freqtrade 설정 생성 실패", error=str(e))
        raise


def validate_system() -> bool:
    """
    시스템 전체 검증을 수행합니다.
    
    Returns:
        bool: 검증 성공 여부
    """
    logger = get_logger(__name__)
    
    try:
        # 1. 설정 검증
        logger.info("시스템 설정 검증 시작")
        config_result = validate_configuration()
        
        if config_result['status'] != 'valid':
            logger.error("설정 검증 실패", error=config_result.get('error'))
            return False
        
        # 2. 디렉토리 구조 확인
        required_dirs = ['data', 'logs', 'strategies', 'config']
        for dir_name in required_dirs:
            dir_path = Path(dir_name)
            if not dir_path.exists():
                logger.warning(f"디렉토리 생성", directory=dir_name)
                dir_path.mkdir(parents=True, exist_ok=True)
        
        # 3. 전략 파일 확인
        strategy_path = Path("strategies/rsi_strategy.py")
        if not strategy_path.exists():
            logger.error("전략 파일이 존재하지 않음", path=str(strategy_path))
            return False
        
        # 4. 의존성 확인 (간단한 import 테스트)
        try:
            import freqtrade
            import ccxt
            import pandas
            import numpy
            logger.info("필수 패키지 확인 완료")
        except ImportError as e:
            logger.error("필수 패키지 누락", package=str(e))
            return False
        
        logger.info("시스템 검증 완료")
        return True
        
    except Exception as e:
        logger.error("시스템 검증 중 오류", error=str(e))
        return False


def run_freqtrade(command: str, config_file: str, additional_args: List[str] = None) -> int:
    """
    Freqtrade 명령을 실행합니다.
    
    Args:
        command (str): 실행할 명령 (trade, backtesting, etc.)
        config_file (str): 설정 파일 경로
        additional_args (List[str], optional): 추가 인수
        
    Returns:
        int: 실행 결과 코드
    """
    logger = get_logger(__name__)
    
    try:
        # 기본 freqtrade 명령 구성
        cmd = ["freqtrade", command, "--config", config_file]
        
        # 추가 인수 추가
        if additional_args:
            cmd.extend(additional_args)
        
        logger.info("Freqtrade 실행", command=" ".join(cmd))
        
        # 프로세스 실행
        result = subprocess.run(cmd, capture_output=False, text=True)
        
        if result.returncode == 0:
            logger.info("Freqtrade 실행 완료", return_code=result.returncode)
        else:
            logger.error("Freqtrade 실행 실패", return_code=result.returncode)
        
        return result.returncode
        
    except Exception as e:
        logger.error("Freqtrade 실행 중 오류", error=str(e))
        return 1


def main():
    """메인 실행 함수."""
    
    # 인수 파서 설정
    parser = argparse.ArgumentParser(
        description="Freqtrade 암호화폐 자동거래 시스템",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예제:
  %(prog)s run --dry-run --strategy RSIStrategy
  %(prog)s backtest --strategy RSIStrategy --timerange 20231201-20240201
  %(prog)s plot --strategy RSIStrategy
  %(prog)s validate
        """
    )
    
    # 서브커맨드 설정
    subparsers = parser.add_subparsers(dest='command', help='사용 가능한 명령들')
    
    # run 명령
    run_parser = subparsers.add_parser('run', help='실시간 거래 실행')
    run_parser.add_argument('--strategy', default='RsiStrategy', help='사용할 전략')
    run_parser.add_argument('--dry-run', action='store_true', help='드라이런 모드')
    
    # backtest 명령  
    backtest_parser = subparsers.add_parser('backtest', help='백테스트 실행')
    backtest_parser.add_argument('--strategy', required=True, help='사용할 전략')
    backtest_parser.add_argument('--timerange', help='백테스트 기간 (예: 20231201-20240201)')
    backtest_parser.add_argument('--timeframe', help='시간프레임 (예: 5m, 1h)')
    
    # plot 명령
    plot_parser = subparsers.add_parser('plot', help='백테스트 결과 차트 생성')
    plot_parser.add_argument('--strategy', required=True, help='차트를 생성할 전략')
    
    # validate 명령
    validate_parser = subparsers.add_parser('validate', help='시스템 검증')
    
    # 인수 파싱
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    try:
        # 로깅 초기화
        initialize_logging()
        logger = get_logger(__name__)
        trading_logger = TradingLogger()
        
        logger.info("Freqtrade 시스템 시작", command=args.command)
        
        # 시스템 검증
        if not validate_system():
            logger.error("시스템 검증 실패")
            return 1
        
        # 설정 로드
        trading_config = get_settings()
        db_config = get_database_config()
        monitor_config = get_monitoring_config()
        
        # 명령별 처리
        if args.command == 'validate':
            logger.info("시스템 검증 완료 - 모든 검사 통과")
            return 0
        
        elif args.command == 'run':
            # 드라이런 모드 설정
            if args.dry_run:
                trading_config.trading_mode = TradingMode.DRY_RUN
            
            # Freqtrade 설정 생성
            freqtrade_config = create_freqtrade_config(
                trading_config, db_config, monitor_config, args.strategy
            )
            
            # 설정 파일 저장
            config_path = "config/freqtrade_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(freqtrade_config, f, indent=2, ensure_ascii=False)
            
            logger.info("거래 시작", strategy=args.strategy, dry_run=args.dry_run)
            
            # Freqtrade 실행
            return run_freqtrade("trade", config_path)
        
        elif args.command == 'backtest':
            # 백테스트 설정
            freqtrade_config = create_freqtrade_config(
                trading_config, db_config, monitor_config, args.strategy
            )
            
            config_path = "config/backtest_config.json"
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(freqtrade_config, f, indent=2, ensure_ascii=False)
            
            # 백테스트 인수 구성
            backtest_args = ["--strategy", args.strategy]
            
            if args.timerange:
                backtest_args.extend(["--timerange", args.timerange])
            
            if args.timeframe:
                backtest_args.extend(["--timeframe", args.timeframe])
            
            logger.info("백테스트 시작", strategy=args.strategy, timerange=args.timerange)
            
            return run_freqtrade("backtesting", config_path, backtest_args)
        
        elif args.command == 'plot':
            # 차트 생성은 별도 처리 필요
            logger.info("차트 생성 기능은 추후 구현 예정")
            return 0
        
        else:
            logger.error("알 수 없는 명령", command=args.command)
            return 1
    
    except KeyboardInterrupt:
        logger.info("사용자에 의해 중단됨")
        return 0
    
    except Exception as e:
        logger.error("실행 중 오류 발생", error=str(e))
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)