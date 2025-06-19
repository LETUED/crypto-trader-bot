#!/usr/bin/env python3
"""
MoniGoMani 전략 드라이런 실행기

실제 거래 없이 MoniGoMani 전략을 시뮬레이션으로 실행합니다.
실시간 데이터를 사용하여 전략의 신호 생성과 거래 로직을 테스트합니다.
"""

import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
import warnings

from strategies.monigomani_strategy import MoniGoManiStrategy
from strategies.optimized_monigomani_strategy import OptimizedMoniGoManiStrategy

warnings.filterwarnings('ignore')

class DryRunTrader:
    """드라이런 거래 시뮬레이터"""
    
    def __init__(self, strategy, initial_balance: float = 10000):
        self.strategy = strategy
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.position = None  # None: 현금, dict: 포지션 정보
        self.trade_history = []
        self.signal_history = []
        self.equity_curve = []
        
        print(f"🚀 드라이런 트레이더 초기화")
        print(f"   💰 초기 자금: ${initial_balance:,.0f}")
        print(f"   📊 전략: {strategy.__class__.__name__}")
    
    def generate_live_data(self, periods: int = 100) -> pd.DataFrame:
        """실시간 데이터를 시뮬레이션합니다."""
        print(f"📊 실시간 데이터 생성 중... ({periods}개 캔들)")
        
        # 현재 시간부터 역산
        end_time = datetime.now()
        start_time = end_time - timedelta(minutes=periods * 15)  # 15분 간격
        
        # periods 파라미터 없이 start와 end만 사용
        dates = pd.date_range(start_time, end_time, freq='15min')
        
        # 실제 생성된 periods 수로 조정
        actual_periods = len(dates)
        print(f"   실제 생성된 캔들 수: {actual_periods}개")
        
        # 현실적인 BTC 가격 시뮬레이션
        base_price = 67000  # 현재 BTC 가격 기준
        current_price = base_price
        
        # 시장 사이클 (상승 → 조정 → 횡보 → 상승)
        cycle_length = actual_periods // 4
        
        data = []
        
        for i, timestamp in enumerate(dates):
            # 시장 사이클에 따른 추세
            cycle_phase = i // cycle_length if cycle_length > 0 else 0
            
            if cycle_phase == 0:  # 초기 상승
                trend = 0.0005
                volatility = 0.015
            elif cycle_phase == 1:  # 조정
                trend = -0.0003
                volatility = 0.025
            elif cycle_phase == 2:  # 횡보
                trend = 0.0001
                volatility = 0.018
            else:  # 재상승
                trend = 0.0007
                volatility = 0.020
            
            # 가격 변동
            noise = np.random.randn() * volatility
            price_change = trend + noise
            
            # OHLC 생성
            open_price = current_price
            close_price = current_price * (1 + price_change)
            
            # 캔들 내 변동성
            intra_vol = abs(price_change) * 1.5
            high_price = max(open_price, close_price) * (1 + intra_vol)
            low_price = min(open_price, close_price) * (1 - intra_vol)
            
            # 거래량 (변동성과 연관)
            base_volume = 2000000
            volume_factor = 1 + abs(price_change) * 20 + np.random.random() * 0.3
            volume = base_volume * volume_factor
            
            data.append({
                'timestamp': timestamp,
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': volume
            })
            
            current_price = close_price
        
        df = pd.DataFrame(data)
        
        print(f"✅ 데이터 생성 완료")
        print(f"   📅 기간: {df['timestamp'].iloc[0]} ~ {df['timestamp'].iloc[-1]}")
        print(f"   💵 가격 범위: ${df['close'].min():,.0f} ~ ${df['close'].max():,.0f}")
        print(f"   📈 총 변동률: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")
        
        return df
    
    def process_signals(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """전략 신호를 처리합니다."""
        print("🔍 전략 신호 분석 중...")
        
        metadata = {'pair': 'BTC/USDT', 'timeframe': '15m'}
        
        # 지표 계산
        df = self.strategy.populate_indicators(dataframe.copy(), metadata)
        
        # 매매 신호 생성
        df = self.strategy.populate_entry_trend(df, metadata)
        df = self.strategy.populate_exit_trend(df, metadata)
        
        # 신호 통계
        buy_signals = df['enter_long'].sum()
        sell_signals = df['exit_long'].sum()
        total_candles = len(df)
        
        print(f"📊 신호 분석 결과:")
        print(f"   📈 매수 신호: {buy_signals}개 ({buy_signals/total_candles*100:.1f}%)")
        print(f"   📉 매도 신호: {sell_signals}개 ({sell_signals/total_candles*100:.1f}%)")
        
        # 가중 신호 분석 (MoniGoMani인 경우)
        if hasattr(df, 'weighted_signal'):
            avg_signal = df['weighted_signal'].mean()
            signal_range = f"{df['weighted_signal'].min():.1f} ~ {df['weighted_signal'].max():.1f}"
            print(f"   ⚖️ 평균 가중신호: {avg_signal:.1f} (범위: {signal_range})")
        
        return df
    
    def simulate_trading(self, dataframe: pd.DataFrame):
        """거래 시뮬레이션을 실행합니다."""
        print("\n🎮 거래 시뮬레이션 시작...")
        print("=" * 50)
        
        for i, row in dataframe.iterrows():
            current_time = row['timestamp']
            current_price = row['close']
            
            # 현재 포트폴리오 가치 계산
            if self.position:
                portfolio_value = self.current_balance * (current_price / self.position['entry_price'])
            else:
                portfolio_value = self.current_balance
            
            self.equity_curve.append({
                'timestamp': current_time,
                'portfolio_value': portfolio_value,
                'price': current_price,
                'position': 'LONG' if self.position else 'CASH'
            })
            
            # 매수 신호 처리
            if row.get('enter_long', 0) == 1 and not self.position:
                self.execute_buy(current_time, current_price, row)
            
            # 매도 신호 처리
            elif self.position and (
                row.get('exit_long', 0) == 1 or 
                self.check_stop_loss(current_price) or 
                self.check_take_profit(current_price)
            ):
                exit_reason = self.determine_exit_reason(row, current_price)
                self.execute_sell(current_time, current_price, exit_reason)
            
            # 신호 기록
            if hasattr(row, 'weighted_signal'):
                self.signal_history.append({
                    'timestamp': current_time,
                    'price': current_price,
                    'weighted_signal': row.get('weighted_signal', 50),
                    'buy_signal': row.get('enter_long', 0),
                    'sell_signal': row.get('exit_long', 0)
                })
    
    def execute_buy(self, timestamp: datetime, price: float, signal_data: pd.Series):
        """매수 주문을 실행합니다."""
        if self.position:
            return  # 이미 포지션이 있으면 무시
        
        # 포지션 크기 계산 (전체 자금 사용)
        position_size = self.current_balance / price
        
        self.position = {
            'entry_time': timestamp,
            'entry_price': price,
            'size': position_size,
            'signal_strength': signal_data.get('weighted_signal', 50)
        }
        
        print(f"🟢 매수 주문 체결!")
        print(f"   📅 시간: {timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"   💵 가격: ${price:,.2f}")
        print(f"   📊 수량: {position_size:.6f} BTC")
        print(f"   ⚖️ 신호강도: {signal_data.get('weighted_signal', 50):.1f}")
        print(f"   💰 투입금액: ${self.current_balance:,.2f}")
    
    def execute_sell(self, timestamp: datetime, price: float, reason: str):
        """매도 주문을 실행합니다."""
        if not self.position:
            return  # 포지션이 없으면 무시
        
        # 수익률 계산
        entry_price = self.position['entry_price']
        pnl_pct = (price / entry_price - 1) * 100
        pnl_amount = self.current_balance * (price / entry_price - 1)
        
        # 새로운 잔고 계산
        new_balance = self.current_balance * (price / entry_price)
        
        # 거래 기록
        trade = {
            'entry_time': self.position['entry_time'],
            'exit_time': timestamp,
            'entry_price': entry_price,
            'exit_price': price,
            'size': self.position['size'],
            'pnl_pct': pnl_pct,
            'pnl_amount': pnl_amount,
            'exit_reason': reason,
            'duration': timestamp - self.position['entry_time'],
            'signal_strength': self.position['signal_strength']
        }
        
        self.trade_history.append(trade)
        self.current_balance = new_balance
        self.position = None
        
        # 결과 출력
        profit_emoji = "🟢" if pnl_pct > 0 else "🔴"
        print(f"{profit_emoji} 매도 주문 체결!")
        print(f"   📅 시간: {timestamp.strftime('%Y-%m-%d %H:%M')}")
        print(f"   💵 가격: ${price:,.2f}")
        print(f"   📊 수익률: {pnl_pct:+.2f}%")
        print(f"   💰 손익: ${pnl_amount:+,.2f}")
        print(f"   🚪 청산사유: {reason}")
        print(f"   ⏱️ 보유시간: {trade['duration']}")
        print(f"   💼 현재잔고: ${self.current_balance:,.2f}")
        print("-" * 40)
    
    def check_stop_loss(self, current_price: float) -> bool:
        """손절매 조건을 확인합니다."""
        if not self.position:
            return False
        
        loss_pct = (current_price / self.position['entry_price'] - 1)
        return loss_pct <= self.strategy.stoploss
    
    def check_take_profit(self, current_price: float) -> bool:
        """익절 조건을 확인합니다."""
        if not self.position:
            return False
        
        profit_pct = (current_price / self.position['entry_price'] - 1)
        
        # ROI 테이블 확인 (간단화)
        if hasattr(self.strategy, 'minimal_roi'):
            for time_str, roi_target in self.strategy.minimal_roi.items():
                if profit_pct >= roi_target:
                    return True
        
        return False
    
    def determine_exit_reason(self, row: pd.Series, current_price: float) -> str:
        """청산 사유를 결정합니다."""
        if row.get('exit_long', 0) == 1:
            return "신호"
        elif self.check_stop_loss(current_price):
            return "손절매"
        elif self.check_take_profit(current_price):
            return "익절"
        else:
            return "기타"
    
    def print_final_report(self):
        """최종 결과 보고서를 출력합니다."""
        print("\n📊 드라이런 결과 보고서")
        print("=" * 60)
        
        # 기본 통계
        total_trades = len(self.trade_history)
        final_balance = self.current_balance
        total_return = (final_balance / self.initial_balance - 1) * 100
        
        print(f"💰 초기 자금: ${self.initial_balance:,.2f}")
        print(f"💼 최종 자금: ${final_balance:,.2f}")
        print(f"📈 총 수익률: {total_return:+.2f}%")
        print(f"📊 총 거래 수: {total_trades}회")
        
        if total_trades > 0:
            # 거래 분석
            winning_trades = [t for t in self.trade_history if t['pnl_pct'] > 0]
            losing_trades = [t for t in self.trade_history if t['pnl_pct'] <= 0]
            
            win_rate = len(winning_trades) / total_trades * 100
            avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['pnl_pct'] for t in losing_trades]) if losing_trades else 0
            
            print(f"🎯 승률: {win_rate:.1f}% ({len(winning_trades)}승 {len(losing_trades)}패)")
            print(f"📈 평균 수익: {avg_win:.2f}%")
            print(f"📉 평균 손실: {avg_loss:.2f}%")
            
            # 보유 시간 분석
            durations = [t['duration'].total_seconds() / 3600 for t in self.trade_history]
            print(f"⏱️ 평균 보유시간: {np.mean(durations):.1f}시간")
            
            # 청산 사유 분석
            exit_reasons = {}
            for trade in self.trade_history:
                reason = trade['exit_reason']
                exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
            
            print("\n🚪 청산 사유 분석:")
            for reason, count in exit_reasons.items():
                print(f"   {reason}: {count}회 ({count/total_trades*100:.1f}%)")
            
            # 최고/최악 거래
            best_trade = max(self.trade_history, key=lambda x: x['pnl_pct'])
            worst_trade = min(self.trade_history, key=lambda x: x['pnl_pct'])
            
            print(f"\n🏆 최고 거래: {best_trade['pnl_pct']:+.2f}% ({best_trade['exit_time'].strftime('%m-%d %H:%M')})")
            print(f"💥 최악 거래: {worst_trade['pnl_pct']:+.2f}% ({worst_trade['exit_time'].strftime('%m-%d %H:%M')})")
        
        # 현재 포지션 상태
        if self.position:
            current_equity = self.equity_curve[-1]
            unrealized_pnl = (current_equity['price'] / self.position['entry_price'] - 1) * 100
            print(f"\n📈 현재 포지션:")
            print(f"   진입가: ${self.position['entry_price']:,.2f}")
            print(f"   현재가: ${current_equity['price']:,.2f}")
            print(f"   미실현 손익: {unrealized_pnl:+.2f}%")
        else:
            print(f"\n💰 현재 상태: 현금 보유 중")


def main():
    """메인 드라이런 실행 함수"""
    print("🎯 MoniGoMani 전략 드라이런 실행")
    print("=" * 50)
    
    # 자동으로 최적화된 전략 선택
    print("✅ MoniGoMani Optimized 전략으로 자동 실행")
    
    # 전략 설정
    config = {
        'exchange': 'binance',
        'stake_currency': 'USDT',
        'dry_run': True
    }
    
    strategy = OptimizedMoniGoManiStrategy(config)
    
    # 드라이런 트레이더 초기화
    trader = DryRunTrader(strategy, initial_balance=10000)
    
    # 데이터 생성 및 처리
    market_data = trader.generate_live_data(periods=200)  # 약 2일치 데이터
    
    # 신호 분석
    processed_data = trader.process_signals(market_data)
    
    # 거래 시뮬레이션
    trader.simulate_trading(processed_data)
    
    # 최종 보고서
    trader.print_final_report()
    
    print("\n🎉 드라이런 완료!")
    print("💡 실제 거래 전에 충분한 테스트와 검증을 권장합니다.")


if __name__ == "__main__":
    main() 