# 🚀 빠른 시작 가이드

## ✅ 설치 및 실행 성공!

축하합니다! Freqtrade 암호화폐 자동거래 시스템이 성공적으로 설치되고 실행되었습니다.

## 📊 현재 실행 상태

### 시스템 상태 확인
```bash
# 프로세스 확인
ps aux | grep freqtrade

# 로그 실시간 모니터링
tail -f logs/freqtrade.log

# API 상태 확인 (인증 필요)
curl http://localhost:8080/api/v1/status
```

### 웹 대시보드 접속
- **URL**: http://localhost:8080
- **사용자명**: freqtrade
- **비밀번호**: freqtrade123

## 🎯 현재 실행 중인 설정

### 거래 설정
- **모드**: 드라이런 (실제 거래 없음)
- **전략**: RsiStrategy (RSI 기반 역추세 매매)
- **거래소**: Binance (샌드박스 모드)
- **최대 동시 거래**: 3개
- **거래당 투자 금액**: 100 USDT
- **시간프레임**: 5분

### 거래 쌍
- BTC/USDT
- ETH/USDT  
- BNB/USDT

## 🛠️ 기본 명령어

### 시스템 제어
```bash
# 시스템 검증
python main.py validate

# 드라이런 시작 (현재 실행 중)
python main.py run --dry-run --strategy RsiStrategy

# 드라이런 중지
pkill -f freqtrade

# 백테스트 실행
python main.py backtest --strategy RsiStrategy --timerange 20231201-20240201
```

### 로그 모니터링
```bash
# 전체 로그 확인
cat logs/freqtrade.log

# 실시간 로그 모니터링
tail -f logs/freqtrade.log

# 거래 신호만 확인
grep "ENTRY\|EXIT" logs/freqtrade.log

# 오류 로그 확인
grep "ERROR\|CRITICAL" logs/freqtrade.log
```

## 📈 성능 모니터링

### 중요 지표 확인
```bash
# 거래 통계 확인 (웹 대시보드에서 더 자세히 볼 수 있음)
grep "TRADE" logs/freqtrade.log | tail -10

# 전략 성능 로그
grep "Strategy" logs/freqtrade.log | tail -5

# 시장 데이터 수신 확인
grep "Performing" logs/freqtrade.log | tail -3
```

### 웹 대시보드 기능
1. **실시간 거래 현황**: 현재 열린 포지션, 수익/손실
2. **거래 내역**: 과거 모든 거래 기록
3. **성능 차트**: 수익률, 승률, 손실폭 등
4. **로그 뷰어**: 실시간 시스템 로그
5. **전략 설정**: 전략 파라미터 조정

## ⚠️ 안전 수칙

### 드라이런 모드에서 확인할 것들
1. **전략 신호 생성**: 매수/매도 신호가 적절히 생성되는가?
2. **리스크 관리**: 손절매, 익절 로직이 작동하는가?
3. **시장 데이터**: 실시간 가격 데이터를 정상 수신하는가?
4. **로그 품질**: 오류나 경고 메시지가 없는가?

### 실제 거래 전 체크리스트
- [ ] 최소 1주일 이상 드라이런 테스트
- [ ] 다양한 시장 상황에서 백테스트 수행
- [ ] API 키 권한 확인 (거래 권한 활성화)
- [ ] 리스크 설정 재검토 (손실 허용 범위)
- [ ] 모니터링 시스템 구축 (알림 설정)

## 🔧 설정 변경

### 거래 설정 수정
`.env` 파일을 편집하여 설정을 변경할 수 있습니다:

```bash
# .env 파일 편집
nano .env

# 주요 설정들
FREQTRADE_TRADING_MODE=dry_run        # live로 변경시 실제 거래
FREQTRADE_MAX_OPEN_TRADES=3           # 최대 동시 거래 수
FREQTRADE_STAKE_AMOUNT=100.0          # 거래당 투자 금액
FREQTRADE_MAX_RISK_PER_TRADE=0.02     # 거래당 최대 리스크 (2%)
```

### 전략 수정
`user_data/strategies/RsiStrategy.py` 파일을 편집하여 전략을 커스터마이징할 수 있습니다.

## 🚨 문제 해결

### 일반적인 문제들

#### 1. 프로세스가 중지됨
```bash
# 프로세스 상태 확인
ps aux | grep freqtrade

# 다시 시작
python main.py run --dry-run --strategy RsiStrategy
```

#### 2. API 연결 오류
```bash
# 로그에서 오류 확인
grep "ERROR.*API\|ERROR.*Exchange" logs/freqtrade.log

# API 키 설정 확인
grep "FREQTRADE_API" .env
```

#### 3. 전략 로딩 실패
```bash
# 전략 관련 오류 확인
grep "Strategy\|ERROR" logs/freqtrade.log

# 전략 파일 확인
ls -la user_data/strategies/
```

#### 4. 메모리 부족
```bash
# 메모리 사용량 확인
ps aux | grep freqtrade | awk '{print $4"%"}'

# 시작 캔들 수 줄이기 (설정에서 startup_candle_count 조정)
```

## 📞 지원 및 문의

### 로그 수집 (문제 신고시)
```bash
# 최근 로그 수집
tail -100 logs/freqtrade.log > debug_log.txt

# 설정 파일 익명화
cp config/freqtrade_config.json config_debug.json
# API 키 등 민감 정보 제거 후 첨부
```

### 유용한 링크
- [Freqtrade 공식 문서](https://www.freqtrade.io/en/stable/)
- [전략 개발 가이드](https://www.freqtrade.io/en/stable/strategy-customization/)
- [백테스트 가이드](https://www.freqtrade.io/en/stable/backtesting/)

---

## 🎉 다음 단계

1. **웹 대시보드 탐색**: http://localhost:8080에서 실시간 데이터 확인
2. **백테스트 실행**: 과거 데이터로 전략 성능 검증
3. **전략 최적화**: 파라미터 조정으로 성능 개선
4. **리스크 관리 강화**: 손절매, 포지션 크기 최적화
5. **실제 거래 준비**: 충분한 테스트 후 라이브 모드 전환

**Happy Trading! 📈🚀**