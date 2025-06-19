# LETUED Crypto Trader - Multi-Strategy Freqtrade Container
FROM python:3.11-slim

# 메타데이터
LABEL maintainer="LETUED <letued@crypto-trader.com>"
LABEL description="Professional cryptocurrency trading system with dual strategies"
LABEL version="1.0.0"

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    wget \
    libffi-dev \
    libssl-dev \
    libblas3 \
    libc6-dev \
    liblapack3 \
    pkg-config \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# TA-Lib 설치 (기술적 분석 라이브러리)
RUN cd /tmp && \
    wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd / && \
    rm -rf /tmp/ta-lib*

# 작업 디렉토리 설정
WORKDIR /app

# Python 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 권한 설정 (실행 스크립트들)
RUN chmod +x freqtrade_config/*.sh

# 데이터 디렉토리 생성
RUN mkdir -p /app/freqtrade_config/logs \
             /app/freqtrade_config/user_data \
             /app/freqtrade_config/backtest_results \
             /app/data \
             /app/logs

# 환경변수 설정
ENV PYTHONPATH=/app
ENV FREQTRADE_CONFIG_PATH=/app/freqtrade_config

# 포트 노출 (API 서버용)
EXPOSE 8080 8081

# 볼륨 설정 (데이터 영속성)
VOLUME ["/app/freqtrade_config/logs", "/app/freqtrade_config/user_data", "/app/data"]

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/api/v1/ping || exit 1

# 시작 스크립트
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 기본 명령어
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["multi-strategy"]