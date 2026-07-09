#!/bin/bash

echo "==============================================="
echo "📊 전략별 상세 성과 비교 분석"
echo "==============================================="
echo "📅 시간: $(date)"
echo ""

# API 설정
MONIGOMANI_URL="http://127.0.0.1:8080/api/v1"
MONIGOMANI_AUTH="-u freqtrader:CHANGE_ME"

RSI_URL="http://127.0.0.1:8081/api/v1"
RSI_AUTH="-u rsitrader:CHANGE_ME"

echo "🎯 전략별 성과 분석 (페어별):"
echo "-----------------------------------------------"

echo "📈 MoniGoMani 전략 - 페어별 성과:"
curl -s $MONIGOMANI_AUTH $MONIGOMANI_URL/performance | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data:
        print('   페어        거래수   평균수익(%)   총수익(USDT)   승률(%)')
        print('   -----------------------------------------------')
        for perf in data[:5]:  # 상위 5개
            pair = perf.get('pair', 'Unknown')
            count = perf.get('count', 0)
            avg_profit = perf.get('profit_mean_pct', 0)
            total_profit = perf.get('profit_abs', 0)
            winrate = perf.get('winrate', 0) * 100 if perf.get('winrate') else 0
            print(f'   {pair:<11} {count:>6}   {avg_profit:>10.2f}   {total_profit:>11.2f}   {winrate:>6.1f}')
    else:
        print('   아직 거래 내역이 없습니다.')
except Exception as e:
    print(f'   데이터를 가져올 수 없습니다: {e}')
"

echo ""
echo "📈 RSI 전략 - 페어별 성과:"
curl -s $RSI_AUTH $RSI_URL/performance | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data:
        print('   페어        거래수   평균수익(%)   총수익(USDT)   승률(%)')
        print('   -----------------------------------------------')
        for perf in data[:5]:  # 상위 5개
            pair = perf.get('pair', 'Unknown')
            count = perf.get('count', 0)
            avg_profit = perf.get('profit_mean_pct', 0)
            total_profit = perf.get('profit_abs', 0)
            winrate = perf.get('winrate', 0) * 100 if perf.get('winrate') else 0
            print(f'   {pair:<11} {count:>6}   {avg_profit:>10.2f}   {total_profit:>11.2f}   {winrate:>6.1f}')
    else:
        print('   아직 거래 내역이 없습니다.')
except Exception as e:
    print(f'   데이터를 가져올 수 없습니다: {e}')
"

echo ""
echo "📊 전략별 상세 통계:"
echo "-----------------------------------------------"

echo "📈 MoniGoMani 전략 통계:"
curl -s $MONIGOMANI_AUTH $MONIGOMANI_URL/profit | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'   • 총 거래수: {data.get(\"trade_count\", 0)}')
    print(f'   • 승률: {data.get(\"winrate\", 0):.1%}')
    print(f'   • 총 수익률: {data.get(\"profit_closed_percent\", 0):.2f}%')
    print(f'   • 총 수익 (USDT): {data.get(\"profit_closed_coin\", 0):.2f}')
    print(f'   • 평균 거래 시간: {data.get(\"avg_duration\", \"N/A\")}')
    print(f'   • 최대 수익: {data.get(\"best_pair_profit_ratio\", 0):.2%}')
    print(f'   • 최대 손실: {data.get(\"worst_pair_profit_ratio\", 0):.2%}')
except Exception as e:
    print(f'   통계를 가져올 수 없습니다: {e}')
"

echo ""
echo "📈 RSI 전략 통계:"
curl -s $RSI_AUTH $RSI_URL/profit | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'   • 총 거래수: {data.get(\"trade_count\", 0)}')
    print(f'   • 승률: {data.get(\"winrate\", 0):.1%}')
    print(f'   • 총 수익률: {data.get(\"profit_closed_percent\", 0):.2f}%')
    print(f'   • 총 수익 (USDT): {data.get(\"profit_closed_coin\", 0):.2f}')
    print(f'   • 평균 거래 시간: {data.get(\"avg_duration\", \"N/A\")}')
    print(f'   • 최대 수익: {data.get(\"best_pair_profit_ratio\", 0):.2%}')
    print(f'   • 최대 손실: {data.get(\"worst_pair_profit_ratio\", 0):.2%}')
except Exception as e:
    print(f'   통계를 가져올 수 없습니다: {e}')
"

echo ""
echo "🔍 최근 거래 내역 (각 전략별 최근 5개):"
echo "-----------------------------------------------"

echo "📈 MoniGoMani 최근 거래:"
curl -s $MONIGOMANI_AUTH $MONIGOMANI_URL/trades?limit=5 | python3 -c "
import sys, json
from datetime import datetime
try:
    data = json.load(sys.stdin)
    if data.get('trades'):
        print('   시간              페어        수익(%)   기간        수익(USDT)')
        print('   -------------------------------------------------------')
        for trade in data['trades'][:5]:
            close_date = trade.get('close_date', '')[:16] if trade.get('close_date') else 'Open'
            pair = trade.get('pair', 'Unknown')
            profit_pct = trade.get('profit_ratio', 0) * 100
            duration = trade.get('trade_duration', 'N/A')
            profit_abs = trade.get('profit_abs', 0)
            print(f'   {close_date:<16} {pair:<11} {profit_pct:>7.2f}   {duration:<10} {profit_abs:>9.2f}')
    else:
        print('   아직 거래 내역이 없습니다.')
except Exception as e:
    print(f'   거래 내역을 가져올 수 없습니다: {e}')
"

echo ""
echo "📈 RSI 최근 거래:"
curl -s $RSI_AUTH $RSI_URL/trades?limit=5 | python3 -c "
import sys, json
from datetime import datetime
try:
    data = json.load(sys.stdin)
    if data.get('trades'):
        print('   시간              페어        수익(%)   기간        수익(USDT)')
        print('   -------------------------------------------------------')
        for trade in data['trades'][:5]:
            close_date = trade.get('close_date', '')[:16] if trade.get('close_date') else 'Open'
            pair = trade.get('pair', 'Unknown')
            profit_pct = trade.get('profit_ratio', 0) * 100
            duration = trade.get('trade_duration', 'N/A')
            profit_abs = trade.get('profit_abs', 0)
            print(f'   {close_date:<16} {pair:<11} {profit_pct:>7.2f}   {duration:<10} {profit_abs:>9.2f}')
    else:
        print('   아직 거래 내역이 없습니다.')
except Exception as e:
    print(f'   거래 내역을 가져올 수 없습니다: {e}')
"

echo ""
echo "==============================================="