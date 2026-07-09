# crypto-trader-bot

> Freqtrade 기반 암호화폐 자동거래 봇. RSI 역추세와 MoniGoMani 조합 전략을 dry-run으로 돌리고 48조합 백테스트로 비교한다. 2025-06, 아카이브.

## 무엇인가

Freqtrade 프레임워크 위에 자체 전략·리스크·백테스트 레이어를 얹은 봇이다. 이 저장소의 한계(남의 프레임워크 위)를 인식하고 이후 [LETRADE_V1](https://github.com/LETUED/LETRADE_V1)에서 자체 아키텍처로 재구축했다.

## 전략

**RSIStrategy** — 역추세 진입
- 진입: RSI < 30, 볼린저밴드 하단 20% 구간, 거래량 평균 1.2배 이상, MACD 히스토그램 상승 전환, 전체 추세가 하락이 아닐 것
- 청산: RSI > 70 또는 밴드 상단, MACD 하락 전환, RSI 다이버전스
- 손절 -4%, 익절은 시간 단계형 (즉시 8% → 15분 4% → 30분 2% → 1시간 1%)

**MoniGoMani** — 8개 기술지표 가중 조합. `freqtrade_config/strategies/MoniGoManiFreqtrade.py`, 최적화 버전은 `strategies/optimized_monigomani_strategy.py`.

## 리스크 관리

`core/risk_manager.py`에 구현된 리스크 로직 (독립 모듈 — dry-run 실거래 실행은 freqtrade가 담당하며 이 모듈은 지표 산출용):

- 포지션 사이징 5종: 고정 금액, 고정 비율(기본 2%), Kelly, 변동성 기반, ATR 기반
- 낙폭 15% 초과 시 critical 경고 상태(12%에서 축소 트리거)
- 연속 손실·시간 기반 손절 규칙

## 백테스트

전략 × 타임프레임 × 기간 조합 48개를 일괄 실행하고 요약 리포트를 뽑는다.

```bash
python comprehensive_backtest.py
python backtest_all_strategies.py
python strategy_summary_report.py
```

## 실행

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
brew install ta-lib             # TA-Lib 시스템 패키지 (문제 시 INSTALL.md)
pip install -r requirements.txt
cp .env.example .env            # API 키·거래 설정 입력

python main.py validate                              # 설정 검증
python main.py run --dry-run --strategy RSIStrategy  # 드라이런
python main.py backtest --strategy RSIStrategy --timerange 20230601-20231201
# 주의: freqtrade CLI 백테스트는 user_data/ 데이터 다운로드·경로 설정이 선행돼야 한다 (미설정 상태 — 위 합성 백테스트 스크립트가 검증 경로)
```

주요 환경변수: `FREQTRADE_API_KEY/SECRET`, `FREQTRADE_EXCHANGE=binance`, `FREQTRADE_TRADING_MODE=dry_run`, `MONITOR_TELEGRAM_*`(알림 선택). 컨테이너 실행은 `INSTALL.md`의 Dockerfile 예시 참고(별도 docker-compose·배포 스크립트는 미포함).

## 결과

2026-07-09 재현 실행 — 단위 테스트 18개 중 16개 통과(2건은 2026 라이브러리 버전 차이로 실패), 전략 비교·시나리오 백테스트(합성 데이터, 시드 고정) 완주. 일부 전략 변형(MoniGoMani Optimized)은 신버전 pandas에서 신호를 내지 못함 — 상세와 전체 출력은 [docs/백테스트증거_2026-07-09.md](docs/백테스트증거_2026-07-09.md).
freqtrade 2026.6·TA-Lib 0.6.8 핀 고정 — `.venv`에 `pip install -r requirements.txt`로 재현.

## 상태

dry-run 검증 단계까지 만들고 중단했다. 실거래 이력 없음. 이후 자체 아키텍처(LETRADE_V1)로 재구축하면서 이 저장소는 그대로 보존.
2026-07 정비: 의존성 핀(3.13 실측)·백테스트 재현 증거·시크릿 플레이스홀더 정리. dry-run 중단·실거래 이력 없음은 그대로.
