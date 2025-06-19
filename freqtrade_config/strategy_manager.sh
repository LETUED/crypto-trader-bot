#!/bin/bash

show_menu() {
    echo "==============================================="
    echo "🚀 다중 전략 관리 시스템"
    echo "==============================================="
    echo ""
    echo "1. 📊 현재 상태 확인"
    echo "2. 🔄 실시간 모니터링 시작"
    echo "3. 📈 전략별 상세 분석"
    echo "4. 🟢 MoniGoMani 전략 시작"
    echo "5. 🟢 RSI 전략 시작"
    echo "6. 🔴 MoniGoMani 전략 중지"
    echo "7. 🔴 RSI 전략 중지"
    echo "8. 🔴 모든 전략 중지"
    echo "9. 📋 로그 파일 보기"
    echo "0. 🚪 종료"
    echo ""
    echo -n "선택하세요 (0-9): "
}

start_monigomani() {
    echo "🟢 MoniGoMani 전략을 시작합니다..."
    if pgrep -f "config.json" > /dev/null; then
        echo "⚠️  MoniGoMani 전략이 이미 실행 중입니다."
    else
        freqtrade trade -c config.json > monigomani.log 2>&1 &
        echo "✅ MoniGoMani 전략이 시작되었습니다. (PID: $!)"
        sleep 3
    fi
}

start_rsi() {
    echo "🟢 RSI 전략을 시작합니다..."
    if pgrep -f "config_rsi.json" > /dev/null; then
        echo "⚠️  RSI 전략이 이미 실행 중입니다."
    else
        freqtrade trade -c config_rsi.json > rsi.log 2>&1 &
        echo "✅ RSI 전략이 시작되었습니다. (PID: $!)"
        sleep 3
    fi
}

stop_monigomani() {
    echo "🔴 MoniGoMani 전략을 중지합니다..."
    PID=$(pgrep -f "config.json")
    if [ ! -z "$PID" ]; then
        kill $PID
        echo "✅ MoniGoMani 전략이 중지되었습니다. (PID: $PID)"
    else
        echo "⚠️  MoniGoMani 전략이 실행되고 있지 않습니다."
    fi
}

stop_rsi() {
    echo "🔴 RSI 전략을 중지합니다..."
    PID=$(pgrep -f "config_rsi.json")
    if [ ! -z "$PID" ]; then
        kill $PID
        echo "✅ RSI 전략이 중지되었습니다. (PID: $PID)"
    else
        echo "⚠️  RSI 전략이 실행되고 있지 않습니다."
    fi
}

stop_all() {
    echo "🔴 모든 전략을 중지합니다..."
    stop_monigomani
    stop_rsi
}

show_logs() {
    echo "📋 로그 파일 선택:"
    echo "1. MoniGoMani 로그"
    echo "2. RSI 로그"
    echo -n "선택하세요 (1-2): "
    read log_choice
    
    case $log_choice in
        1)
            echo "📋 MoniGoMani 로그 (최근 50줄):"
            echo "-----------------------------------------------"
            tail -50 monigomani.log 2>/dev/null || echo "로그 파일이 없습니다."
            ;;
        2)
            echo "📋 RSI 로그 (최근 50줄):"
            echo "-----------------------------------------------"
            tail -50 rsi.log 2>/dev/null || echo "로그 파일이 없습니다."
            ;;
        *)
            echo "❌ 잘못된 선택입니다."
            ;;
    esac
}

while true; do
    clear
    show_menu
    read choice
    
    case $choice in
        1)
            clear
            ./check_multi_status.sh
            echo ""
            echo "아무 키나 누르면 메뉴로 돌아갑니다..."
            read -n 1
            ;;
        2)
            clear
            echo "🔄 실시간 모니터링을 시작합니다. Ctrl+C로 메뉴로 돌아갑니다."
            echo ""
            ./monitor_multi_loop.sh
            ;;
        3)
            clear
            ./strategy_comparison.sh
            echo ""
            echo "아무 키나 누르면 메뉴로 돌아갑니다..."
            read -n 1
            ;;
        4)
            clear
            start_monigomani
            echo ""
            echo "아무 키나 누르면 메뉴로 돌아갑니다..."
            read -n 1
            ;;
        5)
            clear
            start_rsi
            echo ""
            echo "아무 키나 누르면 메뉴로 돌아갑니다..."
            read -n 1
            ;;
        6)
            clear
            stop_monigomani
            echo ""
            echo "아무 키나 누르면 메뉴로 돌아갑니다..."
            read -n 1
            ;;
        7)
            clear
            stop_rsi
            echo ""
            echo "아무 키나 누르면 메뉴로 돌아갑니다..."
            read -n 1
            ;;
        8)
            clear
            stop_all
            echo ""
            echo "아무 키나 누르면 메뉴로 돌아갑니다..."
            read -n 1
            ;;
        9)
            clear
            show_logs
            echo ""
            echo "아무 키나 누르면 메뉴로 돌아갑니다..."
            read -n 1
            ;;
        0)
            echo "👋 프로그램을 종료합니다."
            exit 0
            ;;
        *)
            echo "❌ 잘못된 선택입니다. 아무 키나 누르세요..."
            read -n 1
            ;;
    esac
done