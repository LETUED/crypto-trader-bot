# 🚀 Freqtrade 암호화폐 자동거래 시스템

## 📋 개요

이 프로젝트는 Freqtrade를 기반으로 한 전문적인 암호화폐 자동거래 시스템입니다. 
모듈화된 architecture(아키텍처)와 comprehensive(포괄적인) risk management(리스크 관리)를 통해 
안정적이고 확장 가능한 거래 시스템을 제공합니다.

## ✨ 주요 기능

### 🎯 거래 전략
- **RSI Strategy**: RSI 지표 기반 역추세 매매 전략
- **모듈화된 전략 구조**: 쉬운 전략 추가 및 커스터마이징
- **백테스트 지원**: 과거 데이터를 통한 전략 검증
- **실시간 신호 생성**: 라이브 시장 데이터 기반 거래 신호

### 🛡️ 리스크 관리
- **포지션 크기 자동 계산**: Kelly Criterion, Fixed Percentage 등 다양한 방법
- **손실폭 모니터링**: 실시간 drawdown 추적 및 경고
- **다중 리스크 한계**: 거래당, 포트폴리오 전체 리스크 제한
- **자동 포지션 축소**: 위험 상황시 자동 포지션 조정

### 📊 모니터링 & 로깅
- **구조화된 로깅**: JSON 형태의 상세한 거래 로그
- **실시간 성능 추적**: 승률, 수익률, 샤프 비율 등
- **텔레그램 알림**: 거래 신호 및 중요 이벤트 알림
- **웹 대시보드**: RESTful API를 통한 실시간 모니터링

### 🔧 설정 관리
- **환경변수 기반 설정**: 보안성과 유연성 확보
- **타입 안전성**: Pydantic을 통한 설정 검증
- **다중 환경 지원**: 개발, 테스트, 운영 환경 분리

## 🏗️ 시스템 아키텍처

```
Cryto_Trader/
├── config/                 # 설정 관리
│   ├── __init__.py
│   └── settings.py         # 메인 설정 클래스
├── core/                   # 핵심 비즈니스 로직
│   ├── __init__.py
│   ├── strategy_base.py    # 전략 기본 클래스
│   └── risk_manager.py     # 리스크 관리 시스템
├── strategies/             # 거래 전략들
│   ├── __init__.py
│   └── rsi_strategy.py     # RSI 기반 전략
├── utils/                  # 유틸리티 함수들
│   └── logger.py           # 로깅 시스템
├── data/                   # 데이터 저장소
├── logs/                   # 로그 파일들
├── tests/                  # 테스트 코드
├── main.py                 # 메인 실행 파일
├── requirements.txt        # 의존성 패키지
└── README.md              # 프로젝트 문서
```

## 🚀 설치 및 설정

### 1. 환경 준비

```bash
# Python 3.8+ 필요
python --version

# 프로젝트 클론
git clone <repository-url>
cd Cryto_Trader

# 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# TA-Lib 시스템 패키지 설치 (macOS)
brew install ta-lib

# 의존성 설치
pip install -r requirements.txt
```

**⚠️ 중요**: TA-Lib 설치에 문제가 있다면 `INSTALL.md` 파일을 참조하세요.

### 2. 환경변수 설정

```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (실제 API 키 입력)
nano .env
```

### 3. 필수 설정값

```bash
# 거래소 API 설정
FREQTRADE_API_KEY=your_api_key_here
FREQTRADE_API_SECRET=your_api_secret_here
FREQTRADE_EXCHANGE=binance

# 거래 설정
FREQTRADE_TRADING_MODE=dry_run  # 처음에는 dry_run으로 시작
FREQTRADE_MAX_OPEN_TRADES=3
FREQTRADE_STAKE_AMOUNT=100.0

# 텔레그램 알림 (선택사항)
MONITOR_TELEGRAM_ENABLED=true
MONITOR_TELEGRAM_TOKEN=your_bot_token
MONITOR_TELEGRAM_CHAT_ID=your_chat_id
```

## 🎮 사용법

### 기본 명령어

```bash
# 시스템 검증
python main.py validate

# 드라이런 모드로 거래 시작 (실제 거래 없음)
python main.py run --dry-run --strategy RSIStrategy

# 실제 거래 시작 (주의: 실제 자금 사용)
python main.py run --strategy RSIStrategy

# 백테스트 실행
python main.py backtest --strategy RSIStrategy --timerange 20231201-20240201

# 도움말 확인
python main.py --help
```

### 전략별 사용법

#### RSI Strategy
```bash
# RSI 전략으로 드라이런
python main.py run --dry-run --strategy RSIStrategy

# RSI 전략 백테스트 (6개월)
python main.py backtest --strategy RSIStrategy --timerange 20230601-20231201
```

## 📈 전략 상세 정보

### RSI Strategy

**개념**: RSI(Relative Strength Index) 지표를 활용한 역추세 매매 전략

**매수 조건**:
- RSI < 30 (과매도)
- 볼린저밴드 하단 근처 (하위 20%)
- 거래량 증가 (평균의 1.2배 이상)
- MACD 히스토그램 상승 전환
- 전체 추세가 하락이 아님

**매도 조건**:
- RSI > 70 (과매수)
- 볼린저밴드 상단 근처 (상위 80%)
- MACD 히스토그램 하락 전환
- RSI 다이버전스 감지

**리스크 관리**:
- 손절매: -4%
- 익절: 8% (즉시), 4% (15분), 2% (30분), 1% (1시간)
- 최대 동시 거래: 3개

## 🛡️ 리스크 관리 시스템

### 포지션 크기 계산 방법

1. **Fixed Percentage**: 고정 비율 (기본 2%)
2. **Kelly Criterion**: 수학적 최적화 기법
3. **Volatility Based**: 변동성 기반 조정
4. **ATR Based**: Average True Range 기반

### 보호 메커니즘

- **최대 손실폭 제한**: 15% 도달시 거래 중단
- **연속 손실 보호**: 5거래 중 4거래 손실시 포지션 축소
- **포트폴리오 리스크 제한**: 전체 리스크 10% 이하 유지
- **시간 기반 손절**: 2시간 이상 -3% 손실시 강제 청산

## 📊 모니터링 및 알림

### 로그 분석

```bash
# 로그 파일 위치
tail -f logs/freqtrade.log

# 거래 내역 확인
grep "거래 진입\|거래 청산" logs/freqtrade.log

# 리스크 이벤트 확인
grep "리스크 이벤트" logs/freqtrade.log
```

### 웹 대시보드

거래 시스템 실행 후 다음 URL에서 대시보드 접근:
- URL: http://localhost:8080
- 사용자명: freqtrade
- 비밀번호: freqtrade123

### 텔레그램 알림 설정

1. BotFather에서 텔레그램 봇 생성
2. 봇 토큰 획득
3. 채팅 ID 확인
4. .env 파일에 설정 추가

## 🧪 테스트 및 백테스트

### 전략 테스트

```bash
# 전략 유효성 검사
python -c "from strategies.rsi_strategy import test_rsi_strategy; test_rsi_strategy()"

# 설정 검증
python -c "from config import validate_configuration; print(validate_configuration())"
```

### 백테스트 실행

```bash
# 기본 백테스트 (최근 3개월)
python main.py backtest --strategy RSIStrategy --timerange 20231001-20240101

# 특정 기간 백테스트
python main.py backtest --strategy RSIStrategy --timerange 20230101-20231231

# 다른 시간프레임으로 백테스트
python main.py backtest --strategy RSIStrategy --timeframe 1h --timerange 20231001-20240101
```

## 🔧 커스터마이징

### 새로운 전략 추가

1. `strategies/` 디렉토리에 새 전략 파일 생성
2. `BaseStrategy` 클래스 상속
3. 필수 메서드 구현:
   - `populate_indicators()`
   - `populate_entry_trend()`
   - `populate_exit_trend()`

```python
from core.strategy_base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    def populate_indicators(self, dataframe, metadata):
        # 지표 계산 로직
        return dataframe
    
    def populate_entry_trend(self, dataframe, metadata):
        # 매수 신호 로직
        return dataframe
    
    def populate_exit_trend(self, dataframe, metadata):
        # 매도 신호 로직
        return dataframe
```

### 설정 커스터마이징

`config/settings.py`에서 다음 항목들을 수정할 수 있습니다:

- 거래 쌍 목록
- 리스크 비율
- 최대 동시 거래 수
- 시간프레임
- ROI 설정

## 📋 주의사항

### ⚠️ 실제 거래 전 체크리스트

1. **드라이런 테스트**: 최소 1주일 이상 드라이런 모드로 테스트
2. **백테스트 검증**: 다양한 시장 상황에서 백테스트 수행
3. **소액 테스트**: 실제 거래시 소액으로 시작
4. **리스크 설정 확인**: 손실 허용 범위 내에서 설정
5. **모니터링 준비**: 알림 설정 및 정기적인 확인

### 🚨 리스크 경고

- **투자 리스크**: 암호화폐 거래는 높은 위험을 수반합니다
- **기술적 위험**: 시스템 오류, 네트워크 문제 등이 발생할 수 있습니다
- **시장 위험**: 급격한 시장 변동으로 예상치 못한 손실이 발생할 수 있습니다
- **자동화 위험**: 자동거래 시스템의 한계를 이해하고 사용해야 합니다

## 🛠️ 문제 해결

### 일반적인 문제들

1. **API 연결 오류**
   ```bash
   # API 키 권한 확인
   # 거래소 API 설정에서 거래 권한 활성화
   # IP 화이트리스트 설정 확인
   ```

2. **데이터 로딩 오류**
   ```bash
   # 데이터 디렉토리 권한 확인
   chmod -R 755 data/
   
   # 수동 데이터 다운로드
   freqtrade download-data --exchange binance --pairs BTC/USDT ETH/USDT --timeframes 5m
   ```

3. **메모리 부족**
   ```bash
   # 시작 캔들 수 줄이기
   # 동시 거래 수 제한
   # 불필요한 지표 제거
   ```

### 로그 분석

```bash
# 오류 로그 확인
grep -i "error\|exception" logs/freqtrade.log

# 거래 성과 확인
grep "거래 청산" logs/freqtrade.log | tail -10

# 리스크 이벤트 확인
grep "리스크" logs/freqtrade.log
```

## 📞 지원 및 기여

### 기여 방법

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

### 연락처

- 이슈 리포트: GitHub Issues
- 기능 요청: GitHub Discussions
- 보안 문제: 이메일로 직접 연락

---

**⚠️ 면책 조항**: 이 소프트웨어는 교육 및 연구 목적으로 제공됩니다. 실제 거래에 사용할 경우 발생하는 모든 손실에 대해 개발자는 책임을 지지 않습니다. 자신의 판단과 책임 하에 사용하시기 바랍니다.

**🎯 Happy Trading!** 📈