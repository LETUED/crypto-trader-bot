# crypto-trader-bot

Freqtrade 기반 암호화폐 자동거래 봇. RSI 역추세 전략과 MoniGoMani 조합 전략을 dry-run으로 돌리고, 48개 조합 백테스트로 비교하는 구성이다. 2025-06 작업, 현재는 아카이브.

## 전략

**RSIStrategy** — 역추세 진입
- 진입: RSI < 30, 볼린저밴드 하단 20% 구간, 거래량 평균 1.2배 이상, MACD 히스토그램 상승 전환, 전체 추세가 하락이 아닐 것
- 청산: RSI > 70 또는 밴드 상단, MACD 하락 전환, RSI 다이버전스
- 손절 -4%, 익절은 시간 단계형 (즉시 8% → 15분 4% → 30분 2% → 1시간 1%)

**MoniGoMani** — 8개 기술지표 가중 조합. `freqtrade_config/strategies/MoniGoManiFreqtrade.py`, 최적화 버전은 `strategies/optimized_monigomani_strategy.py`.

## 백테스트

전략 × 타임프레임 × 기간 조합 48개를 일괄 실행하고 요약 리포트를 뽑는다.

```bash
python comprehensive_backtest.py
python backtest_all_strategies.py
python strategy_summary_report.py
```

## 리스크 관리

- 포지션 사이징 4종: 고정 비율(기본 2%), Kelly, 변동성 기반, ATR 기반 (`core/risk_manager.py`)
- 낙폭 15% 도달 시 거래 중단
- 5거래 중 4거래 손실 시 포지션 축소
- 2시간 이상 -3% 지속 시 강제 청산

## 설치

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
brew install ta-lib             # TA-Lib 시스템 패키지 (문제 시 INSTALL.md)
pip install -r requirements.txt
cp .env.example .env            # API 키·거래 설정 입력
```

주요 환경변수: `FREQTRADE_API_KEY/SECRET`, `FREQTRADE_EXCHANGE=binance`, `FREQTRADE_TRADING_MODE=dry_run`, `MONITOR_TELEGRAM_*` (알림 선택).

## 실행

```bash
python main.py validate                                    # 설정 검증
python main.py run --dry-run --strategy RSIStrategy        # 드라이런
python main.py backtest --strategy RSIStrategy --timerange 20230601-20231201
```

Docker 운용은 `docker-compose.yml`과 `docker-entrypoint.sh`(trade/backtest/webserver 모드), 클라우드 배포는 `deploy/` 참고.

## 상태

dry-run 검증 단계까지 만들고 중단했다. 실거래 이력 없음. 이후 자체 아키텍처로 다시 만들면서 이 저장소는 그대로 보존.
