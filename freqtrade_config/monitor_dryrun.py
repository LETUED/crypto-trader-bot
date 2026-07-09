#!/usr/bin/env python3
"""
Freqtrade 드라이런 모니터링 스크립트
실시간으로 봇 상태, 잔고, 거래 현황을 모니터링합니다.
"""

import requests
import json
import time
from datetime import datetime
import os

class FreqtradeMonitor:
    def __init__(self, base_url="http://127.0.0.1:8080", username="freqtrader", password="CHANGE_ME"):
        self.base_url = base_url
        self.auth = (username, password)
        self.session = requests.Session()
        self.session.auth = self.auth
        
    def get_status(self):
        """현재 거래 상태 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/status")
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Status 조회 오류: {e}")
            return []
    
    def get_balance(self):
        """잔고 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/balance")
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            print(f"Balance 조회 오류: {e}")
            return {}
    
    def get_profit(self):
        """수익 현황 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/profit")
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            print(f"Profit 조회 오류: {e}")
            return {}
    
    def get_performance(self):
        """성과 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/performance")
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            print(f"Performance 조회 오류: {e}")
            return []
    
    def get_trades(self, limit=10):
        """최근 거래 내역 조회"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/trades?limit={limit}")
            return response.json() if response.status_code == 200 else {}
        except Exception as e:
            print(f"Trades 조회 오류: {e}")
            return {}
    
    def print_status(self):
        """현재 상태를 포맷팅하여 출력"""
        print("=" * 80)
        print(f"📊 MoniGoMani 드라이런 모니터링 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        # 잔고 정보
        balance = self.get_balance()
        if balance:
            total = balance.get('total', 0)
            total_bot = balance.get('total_bot', 0)
            print(f"💰 잔고: {total:.2f} USDT (봇 관리: {total_bot:.2f} USDT)")
        
        # 수익 정보
        profit = self.get_profit()
        if profit:
            closed_profit = profit.get('profit_closed_percent', 0)
            trade_count = profit.get('trade_count', 0)
            closed_count = profit.get('closed_trade_count', 0)
            winning_trades = profit.get('winning_trades', 0)
            losing_trades = profit.get('losing_trades', 0)
            winrate = profit.get('winrate', 0)
            
            print(f"📈 총 거래: {trade_count}회 (완료: {closed_count}회)")
            print(f"🎯 승률: {winrate:.1f}% ({winning_trades}승 {losing_trades}패)")
            print(f"💵 수익률: {closed_profit:.2f}%")
        
        # 현재 활성 거래
        status = self.get_status()
        if status:
            print(f"🔄 활성 거래: {len(status)}건")
            for trade in status:
                pair = trade.get('pair', 'Unknown')
                profit_pct = trade.get('profit_pct', 0)
                open_date = trade.get('open_date', '')
                print(f"   • {pair}: {profit_pct:.2f}% (시작: {open_date})")
        else:
            print("🔄 활성 거래: 없음")
        
        # 성과 요약
        performance = self.get_performance()
        if performance:
            print("📊 페어별 성과:")
            for perf in performance[:3]:  # 상위 3개만 표시
                pair = perf.get('pair', 'Unknown')
                profit = perf.get('profit_abs', 0)
                count = perf.get('count', 0)
                print(f"   • {pair}: {profit:.2f} USDT ({count}회)")
        
        print("-" * 80)
    
    def monitor(self, interval=30):
        """지속적 모니터링"""
        print("🚀 MoniGoMani 드라이런 모니터링 시작!")
        print(f"📱 {interval}초마다 업데이트됩니다. Ctrl+C로 종료하세요.")
        
        try:
            while True:
                os.system('clear' if os.name == 'posix' else 'cls')
                self.print_status()
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\n👋 모니터링을 종료합니다.")

def main():
    monitor = FreqtradeMonitor()
    
    # 단일 상태 확인
    if len(os.sys.argv) > 1 and os.sys.argv[1] == '--once':
        monitor.print_status()
    else:
        # 지속적 모니터링
        monitor.monitor(interval=30)

if __name__ == "__main__":
    main()