# 🐳 LETUED Crypto Trader - Docker 사용 가이드

## 📋 개요

이 가이드는 LETUED Crypto Trader를 Docker 컨테이너로 실행하는 방법을 설명합니다.

## 🚀 빠른 시작

### 1. 환경 설정

```bash
# 환경변수 파일 복사
cp .env.docker .env

# 필요시 환경변수 수정
nano .env
```

### 2. 기본 실행 (다중 전략)

```bash
# 이미지 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f crypto-trader
```

## 🎯 실행 모드별 사용법

### 다중 전략 모드 (기본)
```bash
# MoniGoMani + RSI 전략 동시 실행
docker-compose up -d crypto-trader

# 상태 확인
docker-compose ps
```

### MoniGoMani 전략만 실행
```bash
# MoniGoMani 전략만 실행
docker-compose --profile monigomani up -d monigomani-only
```

### RSI 전략만 실행
```bash
# RSI 전략만 실행
docker-compose --profile rsi up -d rsi-only
```

### 백테스트 모드
```bash
# 백테스트 컨테이너 시작
docker-compose --profile backtest run --rm backtest

# 컨테이너 내에서 백테스트 실행
freqtrade backtesting -c /app/freqtrade_config/config.json
```

## 📊 모니터링

### API 접근
- **MoniGoMani**: http://localhost:8080
  - 사용자명: `freqtrader`
  - 비밀번호: `SuperSecretPassword`
- **RSI**: http://localhost:8081
  - 사용자명: `rsitrader`
  - 비밀번호: `RSISecretPassword`

### 로그 확인
```bash
# 실시간 로그 확인
docker-compose logs -f crypto-trader

# 특정 서비스 로그
docker-compose logs -f monigomani-only

# 컨테이너 내부 로그 파일
docker exec -it letued-crypto-trader tail -f /app/freqtrade_config/logs/monigomani.log
```

### Grafana 모니터링 (선택사항)
```bash
# 모니터링 대시보드 시작
docker-compose --profile monitoring up -d monitoring

# 접근: http://localhost:3000
# 사용자명: admin
# 비밀번호: ***REMOVED_GRAFANA_PW*** (또는 .env에서 설정한 값)
```

## 🔧 관리 명령어

### 컨테이너 관리
```bash
# 시작
docker-compose up -d

# 중지
docker-compose down

# 재시작
docker-compose restart

# 강제 재빌드
docker-compose up -d --build
```

### 데이터 관리
```bash
# 볼륨 확인
docker volume ls

# 로그 정리
docker-compose exec crypto-trader find /app/freqtrade_config/logs -name "*.log" -mtime +7 -delete

# 백업
docker-compose exec crypto-trader tar -czf /app/backup-$(date +%Y%m%d).tar.gz /app/freqtrade_config/user_data
```

### 디버깅
```bash
# 컨테이너 내부 접근
docker-compose exec crypto-trader bash

# 프로세스 확인
docker-compose exec crypto-trader ps aux

# 설정 확인
docker-compose exec crypto-trader cat /app/freqtrade_config/config.json
```

## 🛡️ 보안 설정

### 환경변수 보안
```bash
# .env 파일 권한 설정
chmod 600 .env

# Git에서 제외 확인
echo ".env" >> .gitignore
```

### 네트워크 보안
```bash
# 외부 접근 제한 (로컬만 허용)
# docker-compose.yml에서 ports를 "127.0.0.1:8080:8080"로 변경
```

## 🚨 문제 해결

### 일반적인 문제들

#### 1. 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :8080
lsof -i :8081

# 포트 변경 (docker-compose.yml 수정)
ports:
  - "8082:8080"  # 8080 대신 8082 사용
```

#### 2. 권한 문제
```bash
# 볼륨 권한 수정
sudo chown -R $(id -u):$(id -g) ./freqtrade_config/logs
sudo chown -R $(id -u):$(id -g) ./freqtrade_config/user_data
```

#### 3. 메모리 부족
```bash
# 메모리 사용량 확인
docker stats

# 메모리 제한 설정 (docker-compose.yml에 추가)
deploy:
  resources:
    limits:
      memory: 1G
```

#### 4. Telegram 연결 실패
```bash
# 환경변수 확인
docker-compose exec crypto-trader env | grep TELEGRAM

# 봇 테스트
docker-compose exec crypto-trader python /app/freqtrade_config/test_telegram.py
```

## 📈 성능 최적화

### 리소스 모니터링
```bash
# 실시간 리소스 사용량
docker stats letued-crypto-trader

# 디스크 사용량
docker system df
```

### 로그 로테이션
```bash
# 로그 크기 제한 설정 (docker-compose.yml에 추가)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

## 🔄 업데이트

### 코드 업데이트
```bash
# Git에서 최신 코드 가져오기
git pull origin main

# 이미지 재빌드 및 재시작
docker-compose down
docker-compose up -d --build
```

### 의존성 업데이트
```bash
# requirements.txt 업데이트 후
docker-compose build --no-cache
docker-compose up -d
```

## 📞 지원

문제가 발생하면 다음을 확인하세요:

1. **로그 확인**: `docker-compose logs -f crypto-trader`
2. **컨테이너 상태**: `docker-compose ps`
3. **리소스 사용량**: `docker stats`
4. **네트워크 연결**: `curl http://localhost:8080/api/v1/ping`

---

**🎯 Happy Trading with LETUED Crypto Trader! 🚀**