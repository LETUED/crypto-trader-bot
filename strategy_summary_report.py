#!/usr/bin/env python3
"""
전략 백테스팅 종합 보고서

모든 구현된 전략의 성능을 종합 분석하고 최종 추천사항을 제공합니다.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any

from strategies.rsi_strategy import RSIStrategy
from strategies.monigomani_strategy import MoniGoManiStrategy
from strategies.optimized_monigomani_strategy import OptimizedMoniGoManiStrategy
from backtest_all_strategies import StrategyBacktester

def main():
    """종합 보고서 생성"""
    print("📊 암호화폐 거래 전략 종합 성능 보고서")
    print("=" * 80)
    print(f"📅 보고서 생성일: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 백테스터 초기화
    backtester = StrategyBacktester(initial_balance=10000)
    config = {
        'exchange': 'binance',
        'stake_currency': 'USDT',
        'dry_run': True
    }
    
    # 전략 등록
    strategies = {
        "RSI_Strategy": RSIStrategy,
        "MoniGoMani_Original": MoniGoManiStrategy,
        "MoniGoMani_Optimized": OptimizedMoniGoManiStrategy
    }
    
    print("📋 전략 등록 중...")
    for name, strategy_class in strategies.items():
        backtester.register_strategy(name, strategy_class, config)
    
    # 다양한 시장 조건에서 테스트
    test_scenarios = [
        {
            "name": "상승장 (Bull Market)",
            "description": "지속적인 상승 추세, 낮은 변동성",
            "periods": 800,
            "volatility": 0.015,
            "trend_factor": 0.0008
        },
        {
            "name": "하락장 (Bear Market)",
            "description": "지속적인 하락 추세, 높은 변동성",
            "periods": 800,
            "volatility": 0.025,
            "trend_factor": -0.0006
        },
        {
            "name": "횡보장 (Sideways Market)",
            "description": "추세 없는 횡보, 중간 변동성",
            "periods": 800,
            "volatility": 0.020,
            "trend_factor": 0.0001
        },
        {
            "name": "고변동성 시장 (High Volatility)",
            "description": "극심한 변동성, 불규칙한 움직임",
            "periods": 800,
            "volatility": 0.035,
            "trend_factor": 0.0003
        }
    ]
    
    all_results = {}
    
    # 각 시나리오별 테스트
    for scenario in test_scenarios:
        print(f"\n🌊 {scenario['name']} 테스트")
        print(f"   📝 {scenario['description']}")
        print("-" * 60)
        
        # 시장 데이터 생성
        market_data = generate_market_scenario(
            periods=scenario['periods'],
            volatility=scenario['volatility'],
            trend_factor=scenario['trend_factor']
        )
        
        # 백테스팅 실행
        scenario_results = backtester.run_all_backtests(market_data)
        all_results[scenario['name']] = scenario_results
        
        # 시나리오별 간단 요약
        print_scenario_summary(scenario['name'], scenario_results)
    
    # 종합 성능 분석
    print("\n📊 종합 성능 분석")
    print("=" * 80)
    comprehensive_analysis = analyze_all_results(all_results)
    
    # 최종 추천사항
    print("\n💡 전략 선택 가이드 및 추천사항")
    print("=" * 80)
    generate_recommendations(comprehensive_analysis)
    
    # 실전 적용 가이드
    print("\n🚀 실전 적용 가이드")
    print("=" * 80)
    practical_guide()
    
    print("\n🎉 종합 보고서 생성 완료!")

def generate_market_scenario(periods: int, volatility: float, trend_factor: float) -> pd.DataFrame:
    """시나리오별 시장 데이터 생성"""
    np.random.seed(42)  # 일관된 결과를 위한 시드 고정
    
    dates = pd.date_range('2024-01-01', periods=periods, freq='15min')
    base_price = 50000
    current_price = base_price
    
    data = []
    
    for i in range(periods):
        # 추세와 노이즈 결합
        noise = np.random.randn() * volatility
        price_change = trend_factor + noise
        
        # OHLC 생성
        open_price = current_price
        close_price = current_price * (1 + price_change)
        
        # 캔들 내 변동성
        intra_vol = abs(price_change) * 1.2
        high_price = max(open_price, close_price) * (1 + intra_vol)
        low_price = min(open_price, close_price) * (1 - intra_vol)
        
        # 거래량
        volume = 1000000 * (1 + abs(price_change) * 10 + np.random.random() * 0.2)
        
        data.append({
            'timestamp': dates[i],
            'open': open_price,
            'high': high_price,
            'low': low_price,
            'close': close_price,
            'volume': volume
        })
        
        current_price = close_price
    
    return pd.DataFrame(data)

def print_scenario_summary(scenario_name: str, results: Dict[str, Any]):
    """시나리오별 요약 출력"""
    print(f"📈 {scenario_name} 결과 요약:")
    
    for strategy_name, result in results.items():
        status = "🔄 활성" if result['total_trades'] > 0 else "😴 비활성"
        print(f"  {status} {strategy_name}: ", end="")
        
        if result['total_trades'] > 0:
            print(f"수익률 {result['total_return']:.1f}% | "
                  f"거래 {result['total_trades']}회 | "
                  f"승률 {result['win_rate']:.1f}%")
        else:
            print("거래 신호 없음")

def analyze_all_results(all_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """모든 결과를 종합 분석"""
    strategy_metrics = {}
    
    # 전략별 성능 집계
    for scenario_name, scenario_results in all_results.items():
        for strategy_name, result in scenario_results.items():
            if strategy_name not in strategy_metrics:
                strategy_metrics[strategy_name] = {
                    'returns': [],
                    'trades': [],
                    'win_rates': [],
                    'sharpe_ratios': [],
                    'max_drawdowns': [],
                    'active_scenarios': 0
                }
            
            metrics = strategy_metrics[strategy_name]
            metrics['returns'].append(result['total_return'])
            metrics['trades'].append(result['total_trades'])
            metrics['win_rates'].append(result['win_rate'])
            metrics['sharpe_ratios'].append(result['sharpe_ratio'])
            metrics['max_drawdowns'].append(result['max_drawdown'])
            
            if result['total_trades'] > 0:
                metrics['active_scenarios'] += 1
    
    # 통계 계산
    analysis = {}
    for strategy_name, metrics in strategy_metrics.items():
        analysis[strategy_name] = {
            'avg_return': np.mean(metrics['returns']),
            'return_std': np.std(metrics['returns']),
            'avg_trades': np.mean(metrics['trades']),
            'avg_win_rate': np.mean(metrics['win_rates']),
            'avg_sharpe': np.mean(metrics['sharpe_ratios']),
            'avg_drawdown': np.mean(metrics['max_drawdowns']),
            'consistency': len([r for r in metrics['returns'] if r > 0]) / len(metrics['returns']),
            'activity_rate': metrics['active_scenarios'] / len(all_results),
            'risk_adjusted_return': np.mean(metrics['returns']) / (np.std(metrics['returns']) + 0.01)
        }
    
    # 결과 출력
    print("🏆 전략별 종합 성능 순위:")
    print("-" * 60)
    
    # 종합 점수로 정렬
    sorted_strategies = sorted(
        analysis.items(),
        key=lambda x: x[1]['avg_return'] * x[1]['activity_rate'] - x[1]['avg_drawdown'] * 0.5,
        reverse=True
    )
    
    for rank, (strategy_name, stats) in enumerate(sorted_strategies, 1):
        print(f"\n{rank}. 📊 {strategy_name}")
        print(f"   💰 평균 수익률: {stats['avg_return']:.2f}% (표준편차: {stats['return_std']:.2f}%)")
        print(f"   📈 평균 거래 수: {stats['avg_trades']:.0f}회")
        print(f"   🎯 평균 승률: {stats['avg_win_rate']:.1f}%")
        print(f"   📊 평균 샤프 비율: {stats['avg_sharpe']:.2f}")
        print(f"   ⚠️ 평균 최대손실: {stats['avg_drawdown']:.2f}%")
        print(f"   🔄 활성 시나리오: {stats['activity_rate']*100:.0f}%")
        print(f"   🎯 수익 일관성: {stats['consistency']*100:.0f}%")
        print(f"   ⚖️ 위험조정수익: {stats['risk_adjusted_return']:.2f}")
    
    return analysis

def generate_recommendations(analysis: Dict[str, Any]):
    """추천사항 생성"""
    print("💡 투자자 성향별 전략 추천:")
    print("-" * 50)
    
    # 최고 성능 전략
    best_return = max(analysis.items(), key=lambda x: x[1]['avg_return'])
    print(f"🏆 최고 수익률: {best_return[0]} ({best_return[1]['avg_return']:.2f}%)")
    
    # 최고 안정성 전략
    best_stability = min(analysis.items(), key=lambda x: x[1]['avg_drawdown'])
    print(f"🛡️ 최고 안정성: {best_stability[0]} (최대손실 {best_stability[1]['avg_drawdown']:.2f}%)")
    
    # 최고 일관성 전략
    best_consistency = max(analysis.items(), key=lambda x: x[1]['consistency'])
    print(f"📊 최고 일관성: {best_consistency[0]} (수익 확률 {best_consistency[1]['consistency']*100:.0f}%)")
    
    print("\n🎯 투자자 유형별 추천:")
    print("-" * 40)
    
    for strategy_name, stats in analysis.items():
        if stats['avg_return'] > 20 and stats['activity_rate'] > 0.5:
            if stats['avg_drawdown'] < 25:
                print(f"✅ {strategy_name}: 균형잡힌 고수익 전략 (적극적 투자자 추천)")
            else:
                print(f"🚀 {strategy_name}: 고위험 고수익 전략 (위험 감수 가능자)")
        elif stats['avg_drawdown'] < 15:
            print(f"🛡️ {strategy_name}: 안정적 전략 (보수적 투자자)")
        elif stats['activity_rate'] < 0.3:
            print(f"😴 {strategy_name}: 비활성 전략 (조정 필요)")

def practical_guide():
    """실전 적용 가이드"""
    print("🔧 실전 적용 시 고려사항:")
    print("-" * 40)
    
    considerations = [
        "💸 거래 수수료: 백테스팅에서는 고려되지 않은 실제 거래 비용",
        "⚡ 슬리피지: 실제 체결가와 예상가의 차이",
        "🕐 지연시간: 신호 생성과 실제 주문 사이의 시간차",
        "💰 자금 관리: 포지션 사이징과 리스크 관리 규칙",
        "🔄 재균형: 시장 조건 변화에 따른 파라미터 조정",
        "📊 모니터링: 실시간 성능 추적 및 이상 감지"
    ]
    
    for consideration in considerations:
        print(f"   {consideration}")
    
    print("\n🚨 위험 관리 수칙:")
    print("-" * 30)
    
    risk_rules = [
        "1. 총 자금의 2-5%만 단일 거래에 투입",
        "2. 일일 최대 손실 한도 설정 (예: 1%)",
        "3. 연속 손실 시 거래 중단 규칙",
        "4. 정기적인 전략 성능 검토",
        "5. 시장 급변 시 수동 개입 준비"
    ]
    
    for rule in risk_rules:
        print(f"   {rule}")
    
    print("\n📈 성능 개선 방향:")
    print("-" * 30)
    
    improvements = [
        "🤖 머신러닝 기반 파라미터 최적화",
        "📊 추가 기술적 지표 통합",
        "🌐 다중 거래소 차익거래",
        "⏰ 다양한 시간프레임 조합",
        "📰 뉴스/센티멘트 분석 통합",
        "🔄 동적 포트폴리오 리밸런싱"
    ]
    
    for improvement in improvements:
        print(f"   {improvement}")

if __name__ == "__main__":
    main() 