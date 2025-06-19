#!/bin/bash

echo "🔄 다중 전략 실시간 모니터링 시작"
echo "📱 30초마다 업데이트됩니다. Ctrl+C로 종료하세요."
echo ""

while true; do
    clear
    ./check_multi_status.sh
    echo ""
    echo "⏰ 다음 업데이트까지 30초..."
    sleep 30
done