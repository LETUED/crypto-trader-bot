#!/usr/bin/env python3
"""
전략 백테스팅 시스템

모든 구현된 전략을 백테스팅하고 성능을 비교 분석합니다.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import json

# 전략 임포트
from strategies.rsi_strategy import RSIStrategy
from strategies.monigomani_strategy import MoniGoManiStrategy

warnings.filterwarnings('ignore')

class StrategyBacktester:
    """전략 백테스팅 클래스"""
    
    def __init__(self, initial_balance: float = 10000):
        self.initial_balance = initial_balance
        self.strategies = {}
        self.results = {}
        
    def register_strategy(self, name: str, strategy_class, config: dict):
        """전략을 등록합니다."""
        try:
            strategy = strategy_class(config)
            self.strategies[name] = strategy
            print(f"✅ {name} 전략 등록 완료")
        except Exception as e:
            print(f"❌ {name} 전략 등록 실패: {e}")
    
    def generate_market_data(self, periods: int = 1000, volatility: float = 0.02) -> pd.DataFrame:
        """현실적인 시장 데이터를 생성합니다."""
        print(f"📊 {periods}개 캔들 시장 데이터 생성 중...")
        
        # 시드 고정으로 재현 가능한 결과
        np.random.seed(42)
        
        # 날짜 생성 (15분 간격)
        start_date = datetime(2024, 1, 1)
        dates = pd.date_range(start_date, periods=periods, freq='15min')
        
        # 기본 설정
        price_base = 50000  # BTC 기준 가격
        current_price = price_base
        
        # 시장 사이클 생성 (상승 → 횡보 → 하락 → 회복)
        cycle_length = periods // 4
        market_phases = []
        
        for i in range(periods):
            phase = i // cycle_length
            if phase == 0:  # 상승장
                trend = 0.0008
                vol_multiplier = 1.0
            elif phase == 1:  # 횡보장
                trend = 0.0001
                vol_multiplier = 0.7
            elif phase == 2:  # 하락장
                trend = -0.0006
                vol_multiplier = 1.3
            else:  # 회복장
                trend = 0.0005
                vol_multiplier = 1.1
            
            market_phases.append(f"phase_{phase}")
        
        # OHLCV 데이터 생성
        opens = []
        highs = []
        lows = []
        closes = []
        volumes = []
        
        for i in range(periods):
            phase = i // cycle_length
            
            # 추세와 노이즈 결합
            if phase == 0:
                trend = 0.0008
                vol_mult = 1.0
            elif phase == 1:
                trend = 0.0001
                vol_mult = 0.7
            elif phase == 2:
                trend = -0.0006
                vol_mult = 1.3
            else:
                trend = 0.0005
                vol_mult = 1.1
            
            noise = np.random.randn() * volatility * vol_mult
            price_change = trend + noise
            
            # OHLC 생성
            open_price = current_price
            close_price = current_price * (1 + price_change)
            
            # 캔들 내 변동성 추가
            intra_volatility = abs(price_change) * 2
            high_price = max(open_price, close_price) * (1 + intra_volatility)
            low_price = min(open_price, close_price) * (1 - intra_volatility)
            
            # 거래량 생성 (변동성과 연관)
            base_volume = 1000000
            volume_factor = 1 + abs(price_change) * 20 + np.random.random() * 0.5
            volume = base_volume * volume_factor
            
            opens.append(open_price)
            highs.append(high_price)
            lows.append(low_price)
            closes.append(close_price)
            volumes.append(volume)
            
            current_price = close_price
        
        df = pd.DataFrame({
            'timestamp': dates,
            'open': opens,
            'high': highs,
            'low': lows,
            'close': closes,
            'volume': volumes,
            'market_phase': market_phases
        })
        
        print(f"✅ 시장 데이터 생성 완료")
        print(f"   - 기간: {df['timestamp'].iloc[0]} ~ {df['timestamp'].iloc[-1]}")
        print(f"   - 가격 범위: ${df['close'].min():.2f} ~ ${df['close'].max():.2f}")
        print(f"   - 총 변동률: {((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100:.2f}%")
        
        return df
    
    def backtest_strategy(self, strategy_name: str, data: pd.DataFrame) -> Dict[str, Any]:
        """개별 전략을 백테스팅합니다."""
        print(f"\n🔍 {strategy_name} 전략 백테스팅 시작...")
        
        strategy = self.strategies[strategy_name]
        metadata = {'pair': 'BTC/USDT', 'timeframe': '15m'}
        
        try:
            # 지표 계산
            df = strategy.populate_indicators(data.copy(), metadata)
            
            # 매매 신호 생성
            df = strategy.populate_entry_trend(df, metadata)
            df = strategy.populate_exit_trend(df, metadata)
            
            # 백테스팅 실행
            results = self._simulate_trading(df, strategy, strategy_name)
            
            print(f"✅ {strategy_name} 백테스팅 완료")
            return results
            
        except Exception as e:
            print(f"❌ {strategy_name} 백테스팅 실패: {e}")
            return self._empty_results(strategy_name)
    
    def _simulate_trading(self, df: pd.DataFrame, strategy, strategy_name: str) -> Dict[str, Any]:
        """거래 시뮬레이션을 실행합니다."""
        balance = self.initial_balance
        position = 0  # 0: 현금, 1: 보유
        entry_price = 0
        trades = []
        equity_curve = []
        
        for i, row in df.iterrows():
            current_price = row['close']
            
            # 매수 신호
            if row.get('enter_long', 0) == 1 and position == 0:
                position = 1
                entry_price = current_price
                entry_time = row['timestamp']
                
            # 매도 신호 또는 손절매/익절
            elif position == 1:
                should_exit = False
                exit_reason = ""
                
                # 매도 신호
                if row.get('exit_long', 0) == 1:
                    should_exit = True
                    exit_reason = "signal"
                
                # 손절매 체크
                elif (current_price / entry_price - 1) <= strategy.stoploss:
                    should_exit = True
                    exit_reason = "stoploss"
                
                # ROI 체크 (간단화)
                elif (current_price / entry_price - 1) >= 0.1:  # 10% 수익
                    should_exit = True
                    exit_reason = "roi"
                
                if should_exit:
                    # 거래 기록
                    pnl_pct = (current_price / entry_price - 1)
                    pnl_amount = balance * pnl_pct
                    balance = balance * (1 + pnl_pct)
                    
                    trade = {
                        'entry_time': entry_time,
                        'exit_time': row['timestamp'],
                        'entry_price': entry_price,
                        'exit_price': current_price,
                        'pnl_pct': pnl_pct * 100,
                        'pnl_amount': pnl_amount,
                        'exit_reason': exit_reason,
                        'duration_hours': (row['timestamp'] - entry_time).total_seconds() / 3600
                    }
                    trades.append(trade)
                    position = 0
            
            # 현재 잔고 계산 (포지션 고려)
            if position == 1:
                current_balance = balance * (current_price / entry_price)
            else:
                current_balance = balance
                
            equity_curve.append({
                'timestamp': row['timestamp'],
                'balance': current_balance,
                'price': current_price,
                'position': position
            })
        
        # 결과 계산
        return self._calculate_metrics(trades, equity_curve, strategy_name)
    
    def _calculate_metrics(self, trades: List[Dict], equity_curve: List[Dict], strategy_name: str) -> Dict[str, Any]:
        """백테스팅 메트릭을 계산합니다."""
        if not trades:
            return self._empty_results(strategy_name)
        
        # 기본 통계
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t['pnl_pct'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        # 수익률 계산
        total_pnl = sum(t['pnl_pct'] for t in trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0
        
        winning_pnls = [t['pnl_pct'] for t in trades if t['pnl_pct'] > 0]
        losing_pnls = [t['pnl_pct'] for t in trades if t['pnl_pct'] < 0]
        
        avg_win = sum(winning_pnls) / len(winning_pnls) if winning_pnls else 0
        avg_loss = sum(losing_pnls) / len(losing_pnls) if losing_pnls else 0
        
        # 최종 잔고
        final_balance = equity_curve[-1]['balance'] if equity_curve else self.initial_balance
        total_return = (final_balance / self.initial_balance - 1) * 100
        
        # 최대 손실 계산
        peak = self.initial_balance
        max_drawdown = 0
        for point in equity_curve:
            if point['balance'] > peak:
                peak = point['balance']
            drawdown = (peak - point['balance']) / peak * 100
            max_drawdown = max(max_drawdown, drawdown)
        
        # 샤프 비율 (간단화)
        returns = []
        for i in range(1, len(equity_curve)):
            ret = (equity_curve[i]['balance'] / equity_curve[i-1]['balance'] - 1) * 100
            returns.append(ret)
        
        sharpe_ratio = 0
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return * np.sqrt(252) if std_return > 0 else 0
        
        return {
            'strategy_name': strategy_name,
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_return': total_return,
            'avg_trade_pnl': avg_pnl,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'final_balance': final_balance,
            'profit_factor': abs(avg_win / avg_loss) if avg_loss != 0 else float('inf'),
            'trades': trades,
            'equity_curve': equity_curve
        }
    
    def _empty_results(self, strategy_name: str) -> Dict[str, Any]:
        """빈 결과를 반환합니다."""
        return {
            'strategy_name': strategy_name,
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': 0,
            'total_return': 0,
            'avg_trade_pnl': 0,
            'avg_win': 0,
            'avg_loss': 0,
            'max_drawdown': 0,
            'sharpe_ratio': 0,
            'final_balance': self.initial_balance,
            'profit_factor': 0,
            'trades': [],
            'equity_curve': []
        }
    
    def run_all_backtests(self, data: pd.DataFrame) -> Dict[str, Any]:
        """모든 전략을 백테스팅합니다."""
        print("🚀 전체 전략 백테스팅 시작...")
        print("=" * 60)
        
        all_results = {}
        
        for strategy_name in self.strategies.keys():
            result = self.backtest_strategy(strategy_name, data)
            all_results[strategy_name] = result
        
        self.results = all_results
        return all_results
    
    def compare_strategies(self) -> pd.DataFrame:
        """전략 성능을 비교합니다."""
        comparison_data = []
        
        for strategy_name, result in self.results.items():
            comparison_data.append({
                'Strategy': strategy_name,
                'Total Return (%)': f"{result['total_return']:.2f}",
                'Win Rate (%)': f"{result['win_rate']:.1f}",
                'Total Trades': result['total_trades'],
                'Avg Trade (%)': f"{result['avg_trade_pnl']:.2f}",
                'Max Drawdown (%)': f"{result['max_drawdown']:.2f}",
                'Sharpe Ratio': f"{result['sharpe_ratio']:.2f}",
                'Profit Factor': f"{result['profit_factor']:.2f}",
                'Final Balance ($)': f"{result['final_balance']:.0f}"
            })
        
        return pd.DataFrame(comparison_data)
    
    def print_detailed_results(self):
        """상세 결과를 출력합니다."""
        print("\n📊 전략 백테스팅 상세 결과")
        print("=" * 80)
        
        for strategy_name, result in self.results.items():
            print(f"\n🎯 {strategy_name.upper()} 전략")
            print("-" * 50)
            print(f"📈 총 수익률: {result['total_return']:.2f}%")
            print(f"💰 최종 잔고: ${result['final_balance']:.0f}")
            print(f"📊 총 거래 수: {result['total_trades']}회")
            print(f"🎯 승률: {result['win_rate']:.1f}% ({result['winning_trades']}승 {result['losing_trades']}패)")
            print(f"📊 평균 거래: {result['avg_trade_pnl']:.2f}%")
            print(f"📈 평균 수익: {result['avg_win']:.2f}%")
            print(f"📉 평균 손실: {result['avg_loss']:.2f}%")
            print(f"⚠️ 최대 손실: {result['max_drawdown']:.2f}%")
            print(f"📊 샤프 비율: {result['sharpe_ratio']:.2f}")
            print(f"💎 수익 팩터: {result['profit_factor']:.2f}")
            
            # 거래 분석
            if result['trades']:
                trades = result['trades']
                durations = [t['duration_hours'] for t in trades]
                print(f"⏱️ 평균 보유 시간: {np.mean(durations):.1f}시간")
                print(f"🔄 최대 보유 시간: {max(durations):.1f}시간")
                print(f"⚡ 최소 보유 시간: {min(durations):.1f}시간")
                
                # 손절매/익절 분석
                exit_reasons = {}
                for trade in trades:
                    reason = trade['exit_reason']
                    exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
                
                print("🚪 청산 사유:")
                for reason, count in exit_reasons.items():
                    print(f"   - {reason}: {count}회 ({count/len(trades)*100:.1f}%)")


def main():
    """메인 백테스팅 실행 함수"""
    print("🎯 암호화폐 거래 전략 종합 백테스팅 시스템")
    print("=" * 60)
    
    # 백테스터 초기화
    backtester = StrategyBacktester(initial_balance=10000)
    
    # 전략 등록
    print("\n📋 전략 등록 중...")
    
    config = {
        'exchange': 'binance',
        'stake_currency': 'USDT',
        'dry_run': True
    }
    
    backtester.register_strategy("RSI_Strategy", RSIStrategy, config)
    backtester.register_strategy("MoniGoMani_Strategy", MoniGoManiStrategy, config)
    
    # 시장 데이터 생성
    print("\n📊 시장 데이터 생성...")
    market_data = backtester.generate_market_data(periods=2000, volatility=0.025)
    
    # 전체 백테스팅 실행
    print("\n🚀 백테스팅 실행...")
    results = backtester.run_all_backtests(market_data)
    
    # 결과 출력
    backtester.print_detailed_results()
    
    # 비교 테이블
    print("\n📊 전략 성능 비교")
    print("=" * 80)
    comparison_df = backtester.compare_strategies()
    print(comparison_df.to_string(index=False))
    
    # 추가 분석
    print("\n🔍 추가 분석")
    print("=" * 50)
    
    best_return = max(results.values(), key=lambda x: x['total_return'])
    best_sharpe = max(results.values(), key=lambda x: x['sharpe_ratio'])
    best_winrate = max(results.values(), key=lambda x: x['win_rate'])
    
    print(f"🏆 최고 수익률: {best_return['strategy_name']} ({best_return['total_return']:.2f}%)")
    print(f"📊 최고 샤프 비율: {best_sharpe['strategy_name']} ({best_sharpe['sharpe_ratio']:.2f})")
    print(f"🎯 최고 승률: {best_winrate['strategy_name']} ({best_winrate['win_rate']:.1f}%)")
    
    print("\n🎉 백테스팅 완료!")


if __name__ == "__main__":
    main() 