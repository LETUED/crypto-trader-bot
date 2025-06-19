#!/usr/bin/env python3
"""
종합 백테스팅 시스템

다양한 timeframe(1m, 3m, 5m, 15m, 30m, 1h)과 
다양한 시장 시나리오(상승장, 하락장, 횡보장, 고변동성)에서
MoniGoMani 전략을 1년간 백테스팅합니다.
"""

import pandas as pd
import numpy as np
import warnings
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import json

from strategies.monigomani_strategy import MoniGoManiStrategy
from strategies.optimized_monigomani_strategy import OptimizedMoniGoManiStrategy

warnings.filterwarnings('ignore')

class ComprehensiveBacktester:
    """종합 백테스팅 시스템"""
    
    def __init__(self):
        self.results = {}
        self.timeframes = {
            '1m': 1,
            '3m': 3, 
            '5m': 5,
            '15m': 15,
            '30m': 30,
            '1h': 60
        }
        
        self.scenarios = {
            'bull_market': '상승장',
            'bear_market': '하락장', 
            'sideways': '횡보장',
            'high_volatility': '고변동성'
        }
        
        print("🚀 종합 백테스팅 시스템 초기화")
        print(f"📊 테스트 timeframe: {list(self.timeframes.keys())}")
        print(f"🎭 테스트 시나리오: {list(self.scenarios.values())}")
    
    def generate_market_data(self, timeframe_minutes: int, scenario: str, periods: int) -> pd.DataFrame:
        """시나리오별 1년간 시장 데이터를 생성합니다."""
        print(f"📊 {scenario} 시나리오 데이터 생성 중... ({timeframe_minutes}분봉, {periods}개)")
        
        # 1년 전부터 현재까지
        end_time = datetime.now()
        start_time = end_time - timedelta(days=365)
        
        # 실제 기간 계산
        total_minutes = periods * timeframe_minutes
        actual_start = end_time - timedelta(minutes=total_minutes)
        
        dates = pd.date_range(actual_start, end_time, periods=periods)
        
        # 시나리오별 기본 설정
        if scenario == 'bull_market':
            base_trend = 0.0008  # 강한 상승 추세
            base_volatility = 0.012
            base_price = 45000
        elif scenario == 'bear_market':
            base_trend = -0.0006  # 강한 하락 추세
            base_volatility = 0.018
            base_price = 75000
        elif scenario == 'sideways':
            base_trend = 0.0001  # 거의 무추세
            base_volatility = 0.015
            base_price = 60000
        else:  # high_volatility
            base_trend = 0.0002
            base_volatility = 0.035  # 매우 높은 변동성
            base_price = 55000
        
        current_price = base_price
        data = []
        
        # 시장 사이클 생성 (계절성 고려)
        cycle_length = periods // 12  # 월별 사이클
        
        for i, timestamp in enumerate(dates):
            # 계절성 효과 (crypto winter/summer)
            month = timestamp.month
            seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * month / 12)
            
            # 사이클 내 위치
            cycle_position = (i % cycle_length) / cycle_length if cycle_length > 0 else 0
            
            # 추세 조정
            if scenario == 'bull_market':
                # 상승장: 초기 급등 → 조정 → 재상승
                if cycle_position < 0.3:
                    trend = base_trend * 1.5 * seasonal_factor
                elif cycle_position < 0.6:
                    trend = base_trend * 0.3 * seasonal_factor
                else:
                    trend = base_trend * 1.2 * seasonal_factor
                    
            elif scenario == 'bear_market':
                # 하락장: 급락 → 반등 → 재하락
                if cycle_position < 0.4:
                    trend = base_trend * 1.3 * seasonal_factor
                elif cycle_position < 0.7:
                    trend = -base_trend * 0.5 * seasonal_factor
                else:
                    trend = base_trend * 1.1 * seasonal_factor
                    
            elif scenario == 'sideways':
                # 횡보장: 주기적 등락
                trend = base_trend * np.sin(4 * np.pi * cycle_position) * seasonal_factor
                
            else:  # high_volatility
                # 고변동성: 불규칙한 급등락
                volatility_spike = 1 + 2 * abs(np.sin(8 * np.pi * cycle_position))
                trend = base_trend * np.random.randn() * volatility_spike * seasonal_factor
            
            # 변동성 조정
            if scenario == 'high_volatility':
                volatility = base_volatility * (1 + abs(np.sin(6 * np.pi * cycle_position)))
            else:
                volatility = base_volatility * seasonal_factor
            
            # 가격 변동 계산
            noise = np.random.randn() * volatility
            price_change = trend + noise
            
            # OHLC 생성
            open_price = current_price
            close_price = current_price * (1 + price_change)
            
            # 캔들 내 변동성
            intra_volatility = abs(price_change) * 1.8
            high_price = max(open_price, close_price) * (1 + intra_volatility)
            low_price = min(open_price, close_price) * (1 - intra_volatility)
            
            # 거래량 (변동성과 연관)
            base_volume = 1500000
            volume_multiplier = 1 + abs(price_change) * 15 + np.random.random() * 0.4
            volume = base_volume * volume_multiplier
            
            data.append({
                'timestamp': timestamp,
                'open': max(open_price, 1000),  # 최소 가격 보장
                'high': max(high_price, 1000),
                'low': max(low_price, 1000),
                'close': max(close_price, 1000),
                'volume': volume
            })
            
            current_price = close_price
        
        df = pd.DataFrame(data)
        
        # 데이터 검증 및 정리
        df = df.dropna()
        df = df[df['close'] > 0]
        
        total_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
        volatility_realized = df['close'].pct_change().std() * np.sqrt(365 * 24 * 60 / timeframe_minutes) * 100
        
        print(f"✅ 데이터 생성 완료")
        print(f"   📅 기간: {df['timestamp'].iloc[0].strftime('%Y-%m-%d')} ~ {df['timestamp'].iloc[-1].strftime('%Y-%m-%d')}")
        print(f"   💵 가격: ${df['close'].iloc[0]:,.0f} → ${df['close'].iloc[-1]:,.0f}")
        print(f"   📈 총 수익률: {total_return:+.2f}%")
        print(f"   📊 연간 변동성: {volatility_realized:.1f}%")
        
        return df
    
    def run_backtest(self, strategy, dataframe: pd.DataFrame, timeframe: str, scenario: str) -> Dict:
        """단일 백테스트를 실행합니다."""
        
        # 전략에 timeframe 정보 추가
        metadata = {
            'pair': 'BTC/USDT', 
            'timeframe': timeframe,
            'scenario': scenario
        }
        
        # 지표 계산
        df = strategy.populate_indicators(dataframe.copy(), metadata)
        
        # 매매 신호 생성
        df = strategy.populate_entry_trend(df, metadata)
        df = strategy.populate_exit_trend(df, metadata)
        
        # 백테스팅 실행
        initial_balance = 10000
        current_balance = initial_balance
        position = None
        trades = []
        equity_curve = []
        
        for i, row in df.iterrows():
            current_price = row['close']
            current_time = row['timestamp']
            
            # 포트폴리오 가치 계산
            if position:
                portfolio_value = current_balance * (current_price / position['entry_price'])
            else:
                portfolio_value = current_balance
            
            equity_curve.append({
                'timestamp': current_time,
                'portfolio_value': portfolio_value,
                'price': current_price
            })
            
            # 매수 신호
            if row.get('enter_long', 0) == 1 and not position:
                position = {
                    'entry_time': current_time,
                    'entry_price': current_price,
                    'size': current_balance / current_price
                }
            
            # 매도 신호 (신호, 손절매, 익절)
            elif position:
                exit_reason = None
                
                if row.get('exit_long', 0) == 1:
                    exit_reason = 'signal'
                else:
                    # 손절매 확인
                    loss_pct = (current_price / position['entry_price'] - 1)
                    if loss_pct <= strategy.stoploss:
                        exit_reason = 'stoploss'
                    
                    # 익절 확인 (간단화)
                    elif hasattr(strategy, 'minimal_roi'):
                        profit_pct = (current_price / position['entry_price'] - 1)
                        for roi_target in strategy.minimal_roi.values():
                            if profit_pct >= roi_target:
                                exit_reason = 'roi'
                                break
                
                if exit_reason:
                    # 거래 기록
                    pnl_pct = (current_price / position['entry_price'] - 1) * 100
                    pnl_amount = current_balance * (current_price / position['entry_price'] - 1)
                    
                    trades.append({
                        'entry_time': position['entry_time'],
                        'exit_time': current_time,
                        'entry_price': position['entry_price'],
                        'exit_price': current_price,
                        'pnl_pct': pnl_pct,
                        'pnl_amount': pnl_amount,
                        'exit_reason': exit_reason,
                        'duration': current_time - position['entry_time']
                    })
                    
                    current_balance *= (current_price / position['entry_price'])
                    position = None
        
        # 결과 계산
        total_trades = len(trades)
        if total_trades > 0:
            winning_trades = [t for t in trades if t['pnl_pct'] > 0]
            win_rate = len(winning_trades) / total_trades * 100
            avg_win = np.mean([t['pnl_pct'] for t in winning_trades]) if winning_trades else 0
            avg_loss = np.mean([t['pnl_pct'] for t in trades if t['pnl_pct'] <= 0])
            avg_duration = np.mean([t['duration'].total_seconds() / 3600 for t in trades])
        else:
            win_rate = 0
            avg_win = 0
            avg_loss = 0
            avg_duration = 0
        
        total_return = (current_balance / initial_balance - 1) * 100
        
        # 샤프 비율 계산
        if len(equity_curve) > 1:
            returns = pd.Series([eq['portfolio_value'] for eq in equity_curve]).pct_change().dropna()
            if returns.std() > 0:
                sharpe_ratio = returns.mean() / returns.std() * np.sqrt(252)  # 연간화
            else:
                sharpe_ratio = 0
        else:
            sharpe_ratio = 0
        
        return {
            'timeframe': timeframe,
            'scenario': scenario,
            'strategy': strategy.__class__.__name__,
            'total_return': total_return,
            'total_trades': total_trades,
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'avg_duration_hours': avg_duration,
            'sharpe_ratio': sharpe_ratio,
            'final_balance': current_balance,
            'max_drawdown': self.calculate_max_drawdown(equity_curve),
            'trades': trades[:10],  # 처음 10개 거래만 저장
            'buy_signals': df['enter_long'].sum(),
            'sell_signals': df['exit_long'].sum()
        }
    
    def calculate_max_drawdown(self, equity_curve: List[Dict]) -> float:
        """최대 낙폭을 계산합니다."""
        if len(equity_curve) < 2:
            return 0
        
        values = [eq['portfolio_value'] for eq in equity_curve]
        peak = values[0]
        max_dd = 0
        
        for value in values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100
            max_dd = max(max_dd, drawdown)
        
        return max_dd
    
    def run_comprehensive_test(self):
        """종합 백테스팅을 실행합니다."""
        print("\n🎯 종합 백테스팅 시작")
        print("=" * 80)
        
        strategies = [
            MoniGoManiStrategy({'exchange': 'binance', 'stake_currency': 'USDT'}),
            OptimizedMoniGoManiStrategy({'exchange': 'binance', 'stake_currency': 'USDT'})
        ]
        
        total_tests = len(self.timeframes) * len(self.scenarios) * len(strategies)
        current_test = 0
        
        for timeframe, minutes in self.timeframes.items():
            # 1년간 데이터 포인트 계산
            periods = 365 * 24 * 60 // minutes  # 1년간의 캔들 수
            
            print(f"\n📊 {timeframe} timeframe 테스트 ({periods:,}개 캔들)")
            print("-" * 60)
            
            for scenario_key, scenario_name in self.scenarios.items():
                print(f"\n🎭 {scenario_name} 시나리오")
                
                # 시장 데이터 생성
                market_data = self.generate_market_data(minutes, scenario_key, periods)
                
                for strategy in strategies:
                    current_test += 1
                    strategy_name = strategy.__class__.__name__
                    
                    print(f"\n[{current_test}/{total_tests}] {strategy_name} 테스트 중...")
                    
                    try:
                        result = self.run_backtest(strategy, market_data, timeframe, scenario_name)
                        
                        # 결과 저장
                        key = f"{timeframe}_{scenario_key}_{strategy_name}"
                        self.results[key] = result
                        
                        # 간단한 결과 출력
                        print(f"   💰 수익률: {result['total_return']:+.2f}%")
                        print(f"   📊 거래수: {result['total_trades']}회")
                        print(f"   🎯 승률: {result['win_rate']:.1f}%")
                        print(f"   📈 샤프: {result['sharpe_ratio']:.2f}")
                        
                    except Exception as e:
                        print(f"   ❌ 오류 발생: {str(e)}")
                        continue
        
        print(f"\n✅ 종합 백테스팅 완료! ({len(self.results)}개 결과)")
        
    def generate_comprehensive_report(self):
        """종합 결과 보고서를 생성합니다."""
        print("\n📊 종합 백테스팅 결과 보고서")
        print("=" * 80)
        
        if not self.results:
            print("❌ 결과 데이터가 없습니다.")
            return
        
        # 1. Timeframe별 성과 분석
        print("\n🕐 Timeframe별 평균 성과")
        print("-" * 50)
        
        timeframe_summary = {}
        for tf in self.timeframes.keys():
            tf_results = [r for k, r in self.results.items() if k.startswith(tf + '_')]
            if tf_results:
                avg_return = np.mean([r['total_return'] for r in tf_results])
                avg_trades = np.mean([r['total_trades'] for r in tf_results])
                avg_winrate = np.mean([r['win_rate'] for r in tf_results])
                avg_sharpe = np.mean([r['sharpe_ratio'] for r in tf_results])
                
                timeframe_summary[tf] = {
                    'avg_return': avg_return,
                    'avg_trades': avg_trades,
                    'avg_winrate': avg_winrate,
                    'avg_sharpe': avg_sharpe
                }
                
                print(f"{tf:>4}: 수익률 {avg_return:+6.2f}% | 거래 {avg_trades:4.0f}회 | 승률 {avg_winrate:4.1f}% | 샤프 {avg_sharpe:5.2f}")
        
        # 2. 시나리오별 성과 분석
        print("\n🎭 시나리오별 평균 성과")
        print("-" * 50)
        
        scenario_summary = {}
        for scenario_key, scenario_name in self.scenarios.items():
            scenario_results = [r for k, r in self.results.items() if scenario_key in k]
            if scenario_results:
                avg_return = np.mean([r['total_return'] for r in scenario_results])
                avg_trades = np.mean([r['total_trades'] for r in scenario_results])
                avg_winrate = np.mean([r['win_rate'] for r in scenario_results])
                avg_sharpe = np.mean([r['sharpe_ratio'] for r in scenario_results])
                
                scenario_summary[scenario_name] = {
                    'avg_return': avg_return,
                    'avg_trades': avg_trades,
                    'avg_winrate': avg_winrate,
                    'avg_sharpe': avg_sharpe
                }
                
                print(f"{scenario_name:>8}: 수익률 {avg_return:+6.2f}% | 거래 {avg_trades:4.0f}회 | 승률 {avg_winrate:4.1f}% | 샤프 {avg_sharpe:5.2f}")
        
        # 3. 전략별 성과 분석
        print("\n🚀 전략별 평균 성과")
        print("-" * 50)
        
        strategy_summary = {}
        for strategy_name in ['MoniGoManiStrategy', 'OptimizedMoniGoManiStrategy']:
            strategy_results = [r for k, r in self.results.items() if strategy_name in k]
            if strategy_results:
                avg_return = np.mean([r['total_return'] for r in strategy_results])
                avg_trades = np.mean([r['total_trades'] for r in strategy_results])
                avg_winrate = np.mean([r['win_rate'] for r in strategy_results])
                avg_sharpe = np.mean([r['sharpe_ratio'] for r in strategy_results])
                
                strategy_summary[strategy_name] = {
                    'avg_return': avg_return,
                    'avg_trades': avg_trades,
                    'avg_winrate': avg_winrate,
                    'avg_sharpe': avg_sharpe
                }
                
                display_name = "Original" if "Optimized" not in strategy_name else "Optimized"
                print(f"{display_name:>12}: 수익률 {avg_return:+6.2f}% | 거래 {avg_trades:4.0f}회 | 승률 {avg_winrate:4.1f}% | 샤프 {avg_sharpe:5.2f}")
        
        # 4. 최고 성과 조합
        print("\n🏆 최고 성과 조합 TOP 10")
        print("-" * 70)
        
        sorted_results = sorted(self.results.items(), key=lambda x: x[1]['total_return'], reverse=True)
        
        for i, (key, result) in enumerate(sorted_results[:10], 1):
            parts = key.split('_')
            timeframe = parts[0]
            scenario = self.scenarios.get(parts[1], parts[1])
            strategy = "Optimized" if "Optimized" in parts[2] else "Original"
            
            print(f"{i:2d}. {timeframe:>4} | {scenario:>8} | {strategy:>10} | "
                  f"{result['total_return']:+7.2f}% | {result['total_trades']:3d}회 | "
                  f"{result['win_rate']:4.1f}% | {result['sharpe_ratio']:5.2f}")
        
        # 5. 최악 성과 조합
        print("\n💥 최악 성과 조합 TOP 5")
        print("-" * 70)
        
        for i, (key, result) in enumerate(sorted_results[-5:], 1):
            parts = key.split('_')
            timeframe = parts[0]
            scenario = self.scenarios.get(parts[1], parts[1])
            strategy = "Optimized" if "Optimized" in parts[2] else "Original"
            
            print(f"{i:2d}. {timeframe:>4} | {scenario:>8} | {strategy:>10} | "
                  f"{result['total_return']:+7.2f}% | {result['total_trades']:3d}회 | "
                  f"{result['win_rate']:4.1f}% | {result['sharpe_ratio']:5.2f}")
        
        # 6. 실전 추천
        print("\n💡 실전 트레이딩 추천")
        print("-" * 50)
        
        # 가장 안정적인 조합 (샤프 비율 기준)
        best_sharpe = max(self.results.items(), key=lambda x: x[1]['sharpe_ratio'])
        best_return = max(self.results.items(), key=lambda x: x[1]['total_return'])
        most_trades = max(self.results.items(), key=lambda x: x[1]['total_trades'])
        
        print("🔹 최고 위험조정수익률:")
        print(f"   {best_sharpe[0]} → 수익률 {best_sharpe[1]['total_return']:+.2f}%, 샤프 {best_sharpe[1]['sharpe_ratio']:.2f}")
        
        print("🔹 최고 절대수익률:")
        print(f"   {best_return[0]} → 수익률 {best_return[1]['total_return']:+.2f}%, 샤프 {best_return[1]['sharpe_ratio']:.2f}")
        
        print("🔹 최다 거래 기회:")
        print(f"   {most_trades[0]} → {most_trades[1]['total_trades']}회 거래, 승률 {most_trades[1]['win_rate']:.1f}%")
        
        # 결과를 JSON으로 저장
        with open('comprehensive_backtest_results.json', 'w', encoding='utf-8') as f:
            # datetime 객체를 문자열로 변환
            serializable_results = {}
            for key, result in self.results.items():
                serializable_result = result.copy()
                # trades에서 datetime 객체 변환
                if 'trades' in serializable_result:
                    for trade in serializable_result['trades']:
                        if 'entry_time' in trade:
                            trade['entry_time'] = trade['entry_time'].isoformat()
                        if 'exit_time' in trade:
                            trade['exit_time'] = trade['exit_time'].isoformat()
                        if 'duration' in trade:
                            trade['duration'] = str(trade['duration'])
                serializable_results[key] = serializable_result
            
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 상세 결과가 'comprehensive_backtest_results.json'에 저장되었습니다.")


def main():
    """메인 실행 함수"""
    print("🎯 MoniGoMani 전략 종합 백테스팅")
    print("다양한 timeframe과 시나리오에서 1년간 성과 분석")
    print("=" * 80)
    
    backtester = ComprehensiveBacktester()
    
    # 종합 백테스팅 실행
    backtester.run_comprehensive_test()
    
    # 결과 보고서 생성
    backtester.generate_comprehensive_report()
    
    print("\n🎉 종합 백테스팅 완료!")
    print("💡 결과를 참고하여 최적의 timeframe과 시장 조건을 선택하세요.")


if __name__ == "__main__":
    main()