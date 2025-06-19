# ☁️ LETUED Crypto Trader - 클라우드 배포 가이드

## 📋 개요

이 가이드는 LETUED Crypto Trader를 클라우드 환경에 배포하는 방법을 설명합니다.

## 🏗️ 지원 플랫폼

### 추천 클라우드 제공업체

1. **DigitalOcean** (추천)
   - Droplet $5/월 (1GB RAM, 25GB SSD)
   - 간단한 설정, 예측 가능한 가격
   - 🔗 [DigitalOcean 가입](https://www.digitalocean.com/)

2. **AWS EC2**
   - t3.micro (프리티어 1년, 1GB RAM)
   - 강력한 생태계, 확장성 우수
   - 🔗 [AWS 가입](https://aws.amazon.com/)

3. **Vultr**
   - VPS $2.50/월 (512MB RAM, 10GB SSD)
   - 가장 저렴한 옵션
   - 🔗 [Vultr 가입](https://www.vultr.com/)

4. **Google Cloud Platform**
   - Compute Engine (300$ 크레딧 제공)
   - 고성능, 글로벌 네트워크
   - 🔗 [GCP 가입](https://cloud.google.com/)

### 최소 시스템 요구사항

- **OS**: Ubuntu 20.04+ 또는 Debian 11+
- **RAM**: 1GB 이상 (2GB 권장)
- **Storage**: 10GB 이상 (25GB 권장)
- **Network**: 인터넷 연결 필수

## 🚀 자동 배포 (추천)

### 1단계: 서버 생성

**DigitalOcean 예시:**
1. [DigitalOcean](https://www.digitalocean.com/) 로그인
2. "Create" → "Droplets" 클릭
3. 설정:
   - **Image**: Ubuntu 22.04 (LTS) x64
   - **Plan**: Basic ($5/월)
   - **CPU**: Regular Intel (1GB/1vCPU/25GB)
   - **Region**: 가까운 지역 선택
   - **Authentication**: SSH Key 추천 (또는 Password)
   - **Hostname**: `letued-crypto-trader`

### 2단계: 서버 접속

```bash
# SSH로 서버 접속
ssh root@YOUR_SERVER_IP

# 또는 일반 사용자로 접속
ssh ubuntu@YOUR_SERVER_IP
```

### 3단계: 자동 배포 스크립트 실행

```bash
# 배포 스크립트 다운로드
curl -fsSL https://raw.githubusercontent.com/LETUED/crypto-trader-bot/main/deploy/cloud-setup.sh -o setup.sh

# 실행 권한 부여
chmod +x setup.sh

# 배포 실행
./setup.sh
```

### 4단계: 프로젝트 설정

```bash
# 프로젝트 디렉토리로 이동
cd /opt/letued-crypto-trader

# 환경변수 설정
cp .env.docker .env
nano .env

# 다음 값들을 수정:
# TELEGRAM_TOKEN=***REMOVED_TELEGRAM_TOKEN***
# TELEGRAM_CHAT_ID=***REMOVED_CHAT_ID***
```

### 5단계: 서비스 시작

```bash
# Docker 컨테이너 시작
docker-compose up -d

# 상태 확인
docker-compose ps
docker-compose logs -f crypto-trader
```

## 🔧 수동 배포

자동 배포가 실패하거나 커스터마이징이 필요한 경우:

### 1. 시스템 업데이트

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Docker 설치

```bash
# Docker 설치
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Docker Compose 설치
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 사용자를 docker 그룹에 추가
sudo usermod -aG docker $USER
```

### 3. 프로젝트 클론

```bash
# Git 설치
sudo apt install -y git

# 프로젝트 클론
git clone https://github.com/LETUED/crypto-trader-bot.git
cd crypto-trader-bot
```

### 4. 환경 설정

```bash
# 환경변수 파일 생성
cp .env.docker .env

# 환경변수 수정
nano .env
```

### 5. 실행

```bash
# Docker 이미지 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f
```

## 🛡️ 보안 설정

### 방화벽 설정

```bash
# UFW 방화벽 활성화
sudo ufw enable

# SSH 허용
sudo ufw allow ssh

# Freqtrade API 포트 (필요시)
sudo ufw allow 8080/tcp
sudo ufw allow 8081/tcp

# 상태 확인
sudo ufw status
```

### SSH 보안 강화

```bash
# SSH 설정 편집
sudo nano /etc/ssh/sshd_config

# 다음 설정 변경:
# PermitRootLogin no
# PasswordAuthentication no  # SSH 키 사용시
# Port 2222  # 기본 포트 변경

# SSH 서비스 재시작
sudo systemctl restart ssh
```

### Fail2Ban 설치

```bash
# Fail2Ban 설치
sudo apt install -y fail2ban

# 기본 설정으로 시작
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

## 📊 모니터링 설정

### 시스템 모니터링

```bash
# htop 설치 (실시간 시스템 모니터링)
sudo apt install -y htop

# 시스템 리소스 확인
htop

# 디스크 사용량 확인
df -h

# 메모리 사용량 확인
free -h
```

### 애플리케이션 모니터링

```bash
# Docker 컨테이너 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f crypto-trader

# 리소스 사용량 확인
docker stats
```

### Grafana 모니터링 (선택사항)

```bash
# Grafana 서비스 시작
docker-compose --profile monitoring up -d monitoring

# 접근: http://YOUR_SERVER_IP:3000
# 기본 로그인: admin / ***REMOVED_GRAFANA_PW***
```

## 🔄 운영 및 유지보수

### 일상적인 관리 명령어

```bash
# 시스템 상태 확인
docker-compose ps

# 로그 확인
docker-compose logs -f crypto-trader

# 컨테이너 재시작
docker-compose restart crypto-trader

# 업데이트 (새 코드 배포)
git pull origin main
docker-compose up -d --build
```

### 백업

```bash
# 설정 파일 백업
tar -czf backup-$(date +%Y%m%d).tar.gz .env freqtrade_config/

# 거래 데이터베이스 백업 (있는 경우)
docker-compose exec crypto-trader cp /app/freqtrade_config/tradesv3.dryrun.sqlite /app/backup/
```

### 로그 관리

```bash
# 로그 크기 확인
du -sh freqtrade_config/logs/

# 오래된 로그 삭제 (7일 이상)
find freqtrade_config/logs/ -name "*.log" -mtime +7 -delete

# Docker 로그 정리
docker system prune -f
```

## 🚨 문제 해결

### 일반적인 문제들

#### 1. 컨테이너가 시작되지 않음

```bash
# 로그 확인
docker-compose logs crypto-trader

# 컨테이너 상태 확인
docker-compose ps

# 강제 재시작
docker-compose down
docker-compose up -d --force-recreate
```

#### 2. 메모리 부족

```bash
# 메모리 사용량 확인
free -h
docker stats

# 스왑 파일 생성 (임시 해결책)
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

#### 3. 디스크 공간 부족

```bash
# 디스크 사용량 확인
df -h

# Docker 정리
docker system prune -a -f

# 로그 파일 정리
find /var/log -name "*.log" -mtime +30 -delete
```

#### 4. 네트워크 연결 문제

```bash
# 방화벽 상태 확인
sudo ufw status

# 포트 확인
netstat -tlnp | grep :8080

# DNS 확인
nslookup google.com
```

## 💰 비용 최적화

### 리소스 최적화

```bash
# 메모리 사용량 제한 (docker-compose.yml에 추가)
deploy:
  resources:
    limits:
      memory: 512M

# 로그 크기 제한
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 자동 종료 설정 (개발/테스트용)

```bash
# 매일 밤 12시에 자동 종료 (cron 설정)
echo "0 0 * * * /sbin/shutdown -h now" | sudo crontab -

# 특정 시간에만 실행 (예: 오전 9시~오후 6시)
echo "0 9 * * * cd /opt/letued-crypto-trader && docker-compose up -d" | crontab -
echo "0 18 * * * cd /opt/letued-crypto-trader && docker-compose down" | crontab -
```

## 📞 지원 및 도움

### 로그 수집

문제 발생시 다음 정보를 수집해주세요:

```bash
# 시스템 정보
uname -a
cat /etc/os-release

# Docker 정보
docker --version
docker-compose --version

# 컨테이너 상태
docker-compose ps
docker-compose logs --tail=50 crypto-trader

# 시스템 리소스
free -h
df -h
```

### 유용한 링크

- **GitHub 저장소**: https://github.com/LETUED/crypto-trader-bot
- **Freqtrade 문서**: https://www.freqtrade.io/
- **Docker 문서**: https://docs.docker.com/

---

**🎯 Happy Cloud Trading with LETUED Crypto Trader! ☁️🚀**