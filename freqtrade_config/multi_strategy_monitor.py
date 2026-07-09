#!/usr/bin/env python3
"""
다중 전략 모니터링 시스템
여러 Freqtrade 봇 인스턴스를 동시에 모니터링합니다.
"""

import requests
import json
import time
from datetime import datetime
import os
import threading
from concurrent.futures import ThreadPoolExecutor
import pandas as pd

class MultiStrategyMonitor:
    def __init__(self):
        self.strategies = {
            'MoniGoMani': {
                'url': 'http://127.0.0.1:8080',
                'auth': ('freqtrader', 'CHANGE_ME'),
                'config': 'config.json',
                'status': 'Unknown'
            },
            'RSI': {
                'url': 'http://127.0.0.1:8081', 
                'auth': ('rsitrader', 'CHANGE_ME'),
                'config': 'config_rsi.json',
                'status': 'Unknown'
            }
        }
        
    def get_strategy_data(self, strategy_name, endpoint):
        """특정 전략의 데이터를 가져옵니다."""
        try:
            strategy = self.strategies[strategy_name]
            url = f"{strategy['url']}/api/v1/{endpoint}"
            response = requests.get(url, auth=strategy['auth'], timeout=5)
            
            if response.status_code == 200:
                self.strategies[strategy_name]['status'] = 'Running'
                return response.json()
            else:
                self.strategies[strategy_name]['status'] = f'Error {response.status_code}'
                return None
                
        except requests.exceptions.ConnectionError:
            self.strategies[strategy_name]['status'] = 'Not Running'
            return None
        except Exception as e:
            self.strategies[strategy_name]['status'] = f'Error: {str(e)}'
            return None
    
    def get_all_data(self):
        """모든 전략의 데이터를 병렬로 가져옵니다."""
        data = {}
        
        with ThreadPoolExecutor(max_workers=len(self.strategies)) as executor:
            # 각 전략별로 필요한 데이터를 병렬로 수집
            futures = {}
            
            for strategy_name in self.strategies.keys():
                futures[f'{strategy_name}_balance'] = executor.submit(
                    self.get_strategy_data, strategy_name, 'balance'
                )
                futures[f'{strategy_name}_profit'] = executor.submit(
                    self.get_strategy_data, strategy_name, 'profit'
                )
                futures[f'{strategy_name}_status'] = executor.submit(
                    self.get_strategy_data, strategy_name, 'status'
                )
                futures[f'{strategy_name}_performance'] = executor.submit(
                    self.get_strategy_data, strategy_name, 'performance'
                )
            
            # 결과 수집
            for strategy_name in self.strategies.keys():
                data[strategy_name] = {
                    'balance': futures[f'{strategy_name}_balance'].result(),
                    'profit': futures[f'{strategy_name}_profit'].result(),
                    'status': futures[f'{strategy_name}_status'].result(),
                    'performance': futures[f'{strategy_name}_performance'].result()
                }
        
        return data
    
    def print_summary(self, data):
        """전략별 요약 정보를 출력합니다."""
        print("=" * 100)
        print(f"🚀 다중 전략 모니터링 대시보드 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 100)
        
        # 전략별 상태 요약
        print("📊 전략 상태 요약:")
        print("-" * 100)
        print(f"{'전략명':<15} {'상태':<12} {'잔고(USDT)':<12} {'거래수':<8} {'승률(%)':<8} {'수익률(%)':<10}")
        print("-" * 100)
        
        total_balance = 0
        total_trades = 0
        total_profit = 0
        
        for strategy_name, strategy_data in data.items():
            status = self.strategies[strategy_name]['status']
            
            if strategy_data['balance']:
                balance = strategy_data['balance'].get('total', 0)
                total_balance += balance
            else:
                balance = 0
            
            if strategy_data['profit']:
                trades = strategy_data['profit'].get('trade_count', 0)
                winrate = strategy_data['profit'].get('winrate', 0)
                profit_pct = strategy_data['profit'].get('profit_closed_percent', 0)
                total_trades += trades
                total_profit += profit_pct
            else:
                trades = 0
                winrate = 0
                profit_pct = 0
            
            print(f"{strategy_name:<15} {status:<12} {balance:<12.2f} {trades:<8} {winrate:<8.1f} {profit_pct:<10.2f}")
        
        print("-" * 100)
        print(f"{'총계':<15} {'':<12} {total_balance:<12.2f} {total_trades:<8} {'':<8} {total_profit:<10.2f}")
        print()
        
        # 활성 거래 상세
        print("🔄 활성 거래 현황:")
        print("-" * 100)
        
        has_active_trades = False
        for strategy_name, strategy_data in data.items():
            if strategy_data['status'] and len(strategy_data['status']) > 0:
                has_active_trades = True
                print(f"📈 {strategy_name} 전략:")
                for trade in strategy_data['status']:
                    pair = trade.get('pair', 'Unknown')
                    profit_pct = trade.get('profit_pct', 0)
                    open_date = trade.get('open_date', '')
                    amount = trade.get('amount', 0)
                    print(f"   • {pair}: {profit_pct:+.2f}% | 수량: {amount:.4f} | 시작: {open_date}")
        
        if not has_active_trades:
            print("   현재 활성 거래가 없습니다.")
        
        print()
        
        # 성과 비교
        print("📊 전략별 성과 비교:")
        print("-" * 100)
        
        for strategy_name, strategy_data in data.items():
            if strategy_data['performance']:
                print(f"📈 {strategy_name} 전략 - 페어별 성과:")
                performance = strategy_data['performance'][:3]  # 상위 3개
                if performance:
                    for perf in performance:
                        pair = perf.get('pair', 'Unknown')
                        profit = perf.get('profit_abs', 0)
                        count = perf.get('count', 0)
                        avg_profit = perf.get('profit_mean_pct', 0)
                        print(f"   • {pair}: {profit:+.2f} USDT ({count}회, 평균 {avg_profit:+.2f}%)")
                else:
                    print("   아직 거래 내역이 없습니다.")
            else:
                print(f"📈 {strategy_name} 전략: 데이터를 가져올 수 없습니다.")
        
        print("-" * 100)
    
    def start_strategies(self):
        """모든 전략을 시작합니다."""
        print("🚀 다중 전략 시작 중...")
        
        # MoniGoMani 전략이 이미 실행 중인지 확인
        monigomani_running = self.get_strategy_data('MoniGoMani', 'balance') is not None
        
        if not monigomani_running:
            print("📊 MoniGoMani 전략 시작 중...")
            os.system("freqtrade trade -c config.json > monigomani.log 2>&1 &")
            time.sleep(3)
        else:
            print("✅ MoniGoMani 전략이 이미 실행 중입니다.")
        
        # RSI 전략 시작
        rsi_running = self.get_strategy_data('RSI', 'balance') is not None
        
        if not rsi_running:
            print("📊 RSI 전략 시작 중...")
            os.system("freqtrade trade -c config_rsi.json > rsi.log 2>&1 &")
            time.sleep(3)
        else:
            print("✅ RSI 전략이 이미 실행 중입니다.")
        
        print("⏳ 전략들이 초기화될 때까지 잠시 기다립니다...")
        time.sleep(10)
    
    def monitor(self, interval=30, auto_start=False):
        """지속적 모니터링을 시작합니다."""
        if auto_start:
            self.start_strategies()
        
        print("🔄 다중 전략 모니터링 시작!")
        print(f"📱 {interval}초마다 업데이트됩니다. Ctrl+C로 종료하세요.")
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                data = self.get_all_data()
                self.print_summary(data)
                
                print(f"⏰ 다음 업데이트까지 {interval}초...")
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n👋 모니터링을 종료합니다.")
    
    def single_check(self):
        """한 번만 상태를 체크합니다."""
        data = self.get_all_data()
        self.print_summary(data)

def main():
    import sys
    
    monitor = MultiStrategyMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--start':
            monitor.start_strategies()
        elif sys.argv[1] == '--once':
            monitor.single_check()
        elif sys.argv[1] == '--monitor':
            monitor.monitor(interval=30, auto_start=False)
        elif sys.argv[1] == '--auto':
            monitor.monitor(interval=30, auto_start=True)
    else:
        print("사용법:")
        print("  python3 multi_strategy_monitor.py --start     # 모든 전략 시작")
        print("  python3 multi_strategy_monitor.py --once     # 한 번 상태 확인")
        print("  python3 multi_strategy_monitor.py --monitor  # 지속적 모니터링")
        print("  python3 multi_strategy_monitor.py --auto     # 자동 시작 + 모니터링")

if __name__ == "__main__":
    main()