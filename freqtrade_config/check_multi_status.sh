#!/bin/bash

echo "==============================================="
echo "🚀 다중 전략 드라이런 상태 체크"
echo "==============================================="
echo "📅 시간: $(date)"
echo ""

# API 설정
MONIGOMANI_URL="http://127.0.0.1:8080/api/v1"
MONIGOMANI_AUTH="-u freqtrader:CHANGE_ME"

RSI_URL="http://127.0.0.1:8081/api/v1"
RSI_AUTH="-u rsitrader:CHANGE_ME"

echo "📊 전략별 상태 요약:"
echo "-----------------------------------------------"
printf "%-15s %-12s %-12s %-8s %-8s %-10s\n" "전략명" "상태" "잔고(USDT)" "거래수" "승률(%)" "수익률(%)"
echo "-----------------------------------------------"

# MoniGoMani 전략 상태
echo -n "MoniGoMani      "
MONI_STATUS=$(curl -s $MONIGOMANI_AUTH $MONIGOMANI_URL/balance 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$MONI_STATUS" ]; then
    echo -n "Running      "
    echo "$MONI_STATUS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    balance = data.get('total', 0)
    print(f'{balance:>11.2f}', end='')
except:
    print('     Error  ', end='')
"
    
    # 수익 정보
    curl -s $MONIGOMANI_AUTH $MONIGOMANI_URL/profit | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    trades = data.get('trade_count', 0)
    winrate = data.get('winrate', 0)
    profit = data.get('profit_closed_percent', 0)
    print(f' {trades:>7} {winrate:>7.1f} {profit:>9.2f}')
except:
    print('      0     0.0      0.00')
"
else
    echo "Not Running       0.00       0     0.0      0.00"
fi

# RSI 전략 상태
echo -n "RSI             "
RSI_STATUS=$(curl -s $RSI_AUTH $RSI_URL/balance 2>/dev/null)
if [ $? -eq 0 ] && [ ! -z "$RSI_STATUS" ]; then
    echo -n "Running      "
    echo "$RSI_STATUS" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    balance = data.get('total', 0)
    print(f'{balance:>11.2f}', end='')
except:
    print('     Error  ', end='')
"
    
    # 수익 정보
    curl -s $RSI_AUTH $RSI_URL/profit | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    trades = data.get('trade_count', 0)
    winrate = data.get('winrate', 0)
    profit = data.get('profit_closed_percent', 0)
    print(f' {trades:>7} {winrate:>7.1f} {profit:>9.2f}')
except:
    print('      0     0.0      0.00')
"
else
    echo "Not Running       0.00       0     0.0      0.00"
fi

echo "-----------------------------------------------"
echo ""

echo "🔄 활성 거래 현황:"
echo "-----------------------------------------------"

# MoniGoMani 활성 거래
echo "📈 MoniGoMani 전략:"
MONI_TRADES=$(curl -s $MONIGOMANI_AUTH $MONIGOMANI_URL/status 2>/dev/null)
if [ "$MONI_TRADES" = "[]" ] || [ -z "$MONI_TRADES" ]; then
    echo "   현재 활성 거래가 없습니다."
else
    echo "$MONI_TRADES" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data:
        for trade in data:
            pair = trade.get('pair', 'Unknown')
            profit = trade.get('profit_pct', 0)
            date = trade.get('open_date', '')
            amount = trade.get('amount', 0)
            print(f'   • {pair}: {profit:+.2f}% | 수량: {amount:.4f} | 시작: {date}')
    else:
        print('   현재 활성 거래가 없습니다.')
except:
    print('   거래 정보를 가져올 수 없습니다.')
"
fi

# RSI 활성 거래
echo "📈 RSI 전략:"
RSI_TRADES=$(curl -s $RSI_AUTH $RSI_URL/status 2>/dev/null)
if [ "$RSI_TRADES" = "[]" ] || [ -z "$RSI_TRADES" ]; then
    echo "   현재 활성 거래가 없습니다."
else
    echo "$RSI_TRADES" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data:
        for trade in data:
            pair = trade.get('pair', 'Unknown')
            profit = trade.get('profit_pct', 0)
            date = trade.get('open_date', '')
            amount = trade.get('amount', 0)
            print(f'   • {pair}: {profit:+.2f}% | 수량: {amount:.4f} | 시작: {date}')
    else:
        print('   현재 활성 거래가 없습니다.')
except:
    print('   거래 정보를 가져올 수 없습니다.')
"
fi

echo ""
echo "📊 실행 중인 프로세스:"
echo "-----------------------------------------------"
ps aux | grep -E "(freqtrade|config)" | grep -v grep | while read line; do
    if [[ $line == *"config.json"* ]]; then
        echo "   🟢 MoniGoMani: $(echo $line | awk '{print $2}')"
    elif [[ $line == *"config_rsi.json"* ]]; then
        echo "   🟢 RSI: $(echo $line | awk '{print $2}')"
    fi
done

echo ""
echo "==============================================="