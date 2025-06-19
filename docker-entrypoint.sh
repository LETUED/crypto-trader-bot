#!/bin/bash
set -e

# LETUED Crypto Trader Docker Entrypoint Script
echo "🚀 LETUED Crypto Trader 시작 중..."
echo "📅 시작 시간: $(date)"

# 환경변수 확인
echo "🔧 환경 설정 확인 중..."
if [ -z "$TELEGRAM_TOKEN" ]; then
    echo "⚠️  TELEGRAM_TOKEN이 설정되지 않았습니다."
fi

if [ -z "$TELEGRAM_CHAT_ID" ]; then
    echo "⚠️  TELEGRAM_CHAT_ID가 설정되지 않았습니다."
fi

# 로그 디렉토리 확인
mkdir -p /app/freqtrade_config/logs
mkdir -p /app/freqtrade_config/user_data
mkdir -p /app/logs

# 권한 설정
chown -R $(id -u):$(id -g) /app/freqtrade_config/logs
chown -R $(id -u):$(id -g) /app/freqtrade_config/user_data

echo "📂 디렉토리 구조 확인 완료"

# 실행 모드에 따른 분기
case "$1" in
    "multi-strategy")
        echo "🎯 다중 전략 모드로 시작합니다..."
        echo "   - MoniGoMani 전략 (포트 8080)"
        echo "   - RSI 전략 (포트 8081)"
        
        # MoniGoMani 전략 시작 (백그라운드)
        echo "🔄 MoniGoMani 전략 시작 중..."
        freqtrade trade -c /app/freqtrade_config/config.json > /app/freqtrade_config/logs/monigomani.log 2>&1 &
        MONIGOMANI_PID=$!
        echo "   MoniGoMani PID: $MONIGOMANI_PID"
        
        # 잠시 대기
        sleep 5
        
        # RSI 전략 시작 (백그라운드)
        echo "🔄 RSI 전략 시작 중..."
        freqtrade trade -c /app/freqtrade_config/config_rsi.json > /app/freqtrade_config/logs/rsi.log 2>&1 &
        RSI_PID=$!
        echo "   RSI PID: $RSI_PID"
        
        # PID 저장
        echo $MONIGOMANI_PID > /app/freqtrade_config/monigomani.pid
        echo $RSI_PID > /app/freqtrade_config/rsi.pid
        
        echo "✅ 모든 전략이 시작되었습니다!"
        echo "📊 모니터링: http://localhost:8080 (MoniGoMani), http://localhost:8081 (RSI)"
        
        # 프로세스 모니터링 및 대기
        while true; do
            if ! kill -0 $MONIGOMANI_PID 2>/dev/null; then
                echo "❌ MoniGoMani 전략이 중단되었습니다!"
                exit 1
            fi
            
            if ! kill -0 $RSI_PID 2>/dev/null; then
                echo "❌ RSI 전략이 중단되었습니다!"
                exit 1
            fi
            
            sleep 30
        done
        ;;
        
    "monigomani-only")
        echo "🎯 MoniGoMani 전략만 시작합니다..."
        exec freqtrade trade -c /app/freqtrade_config/config.json
        ;;
        
    "rsi-only")
        echo "🎯 RSI 전략만 시작합니다..."
        exec freqtrade trade -c /app/freqtrade_config/config_rsi.json
        ;;
        
    "backtest")
        echo "📊 백테스트 모드로 시작합니다..."
        if [ -z "$2" ]; then
            echo "❌ 전략을 지정해주세요: monigomani 또는 rsi"
            exit 1
        fi
        
        if [ "$2" = "monigomani" ]; then
            exec freqtrade backtesting -c /app/freqtrade_config/config.json
        elif [ "$2" = "rsi" ]; then
            exec freqtrade backtesting -c /app/freqtrade_config/config_rsi.json
        else
            echo "❌ 알 수 없는 전략: $2"
            exit 1
        fi
        ;;
        
    "bash")
        echo "🐚 Bash 셸로 시작합니다..."
        exec /bin/bash
        ;;
        
    *)
        echo "🔧 사용법:"
        echo "  multi-strategy    : 다중 전략 실행 (기본값)"
        echo "  monigomani-only   : MoniGoMani 전략만 실행"
        echo "  rsi-only          : RSI 전략만 실행"
        echo "  backtest [strategy]: 백테스트 실행"
        echo "  bash              : Bash 셸 실행"
        exit 1
        ;;
esac