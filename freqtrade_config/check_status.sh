#!/bin/bash

echo "==============================================="
echo "🚀 MoniGoMani 드라이런 상태 체크"
echo "==============================================="
echo "📅 시간: $(date)"
echo ""

# API 기본 설정
API_URL="http://127.0.0.1:8080/api/v1"
AUTH="-u freqtrader:CHANGE_ME"

echo "💰 잔고 정보:"
curl -s $AUTH $API_URL/balance | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    total = data.get('total', 0)
    total_bot = data.get('total_bot', 0)
    print(f'   총 잔고: {total:.2f} USDT')
    print(f'   봇 관리: {total_bot:.2f} USDT')
except:
    print('   잔고 정보를 가져올 수 없습니다.')
"
echo ""

echo "📈 수익 정보:"
curl -s $AUTH $API_URL/profit | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    trade_count = data.get('trade_count', 0)
    closed_count = data.get('closed_trade_count', 0)
    winning = data.get('winning_trades', 0)
    losing = data.get('losing_trades', 0)
    winrate = data.get('winrate', 0)
    profit_pct = data.get('profit_closed_percent', 0)
    
    print(f'   총 거래: {trade_count}회 (완료: {closed_count}회)')
    print(f'   승률: {winrate:.1f}% ({winning}승 {losing}패)')
    print(f'   수익률: {profit_pct:.2f}%')
except:
    print('   수익 정보를 가져올 수 없습니다.')
"
echo ""

echo "🔄 활성 거래:"
ACTIVE_TRADES=$(curl -s $AUTH $API_URL/status)
if [ "$ACTIVE_TRADES" = "[]" ]; then
    echo "   현재 활성 거래가 없습니다."
else
    echo "$ACTIVE_TRADES" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data:
        print(f'   활성 거래: {len(data)}건')
        for trade in data:
            pair = trade.get('pair', 'Unknown')
            profit = trade.get('profit_pct', 0)
            date = trade.get('open_date', '')
            print(f'   • {pair}: {profit:.2f}% (시작: {date})')
    else:
        print('   현재 활성 거래가 없습니다.')
except:
    print('   거래 정보를 가져올 수 없습니다.')
"
fi
echo ""

echo "📊 봇 상태:"
curl -s $AUTH $API_URL/show_config | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    state = data.get('state', 'Unknown')
    strategy = data.get('strategy', 'Unknown')
    max_trades = data.get('max_open_trades', 0)
    
    print(f'   상태: {state}')
    print(f'   전략: {strategy}')
    print(f'   최대 거래: {max_trades}개')
except:
    print('   봇 상태를 가져올 수 없습니다.')
"

echo ""
echo "==============================================="