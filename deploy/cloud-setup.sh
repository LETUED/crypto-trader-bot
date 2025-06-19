#!/bin/bash

# LETUED Crypto Trader - 클라우드 배포 자동화 스크립트
# 지원 플랫폼: Ubuntu 20.04+ (AWS EC2, DigitalOcean, Vultr 등)

set -e

echo "🚀 LETUED Crypto Trader 클라우드 배포 시작"
echo "=================================================="

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 로그 함수
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 시스템 정보 확인
check_system() {
    log_info "시스템 정보 확인 중..."
    
    # OS 확인
    if [[ -f /etc/os-release ]]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
        log_info "OS: $OS $VER"
    else
        log_error "지원하지 않는 운영체제입니다."
        exit 1
    fi
    
    # 메모리 확인
    MEMORY=$(free -m | awk 'NR==2{printf "%.1f", $2/1024}')
    log_info "메모리: ${MEMORY}GB"
    
    if (( $(echo "$MEMORY < 1.0" | bc -l) )); then
        log_warning "메모리가 1GB 미만입니다. 성능에 영향을 줄 수 있습니다."
    fi
    
    # 디스크 공간 확인
    DISK=$(df -h / | awk 'NR==2 {print $4}')
    log_info "사용 가능한 디스크 공간: $DISK"
}

# 필수 패키지 설치
install_dependencies() {
    log_info "필수 패키지 설치 중..."
    
    # 패키지 목록 업데이트
    sudo apt-get update
    
    # 필수 패키지 설치
    sudo apt-get install -y \
        curl \
        wget \
        git \
        unzip \
        htop \
        ufw \
        fail2ban \
        logrotate \
        cron \
        bc
    
    log_success "필수 패키지 설치 완료"
}

# Docker 설치
install_docker() {
    log_info "Docker 설치 중..."
    
    # 기존 Docker 제거
    sudo apt-get remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Docker 공식 GPG 키 추가
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Docker 저장소 추가
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Docker 설치
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Docker 서비스 시작 및 활성화
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 현재 사용자를 docker 그룹에 추가
    sudo usermod -aG docker $USER
    
    log_success "Docker 설치 완료"
}

# 메인 실행 함수
main() {
    echo "🎯 LETUED Crypto Trader 클라우드 배포를 시작합니다."
    echo "이 스크립트는 다음 작업을 수행합니다:"
    echo "1. 시스템 정보 확인"
    echo "2. 필수 패키지 설치"
    echo "3. Docker 설치"
    echo "4. 방화벽 및 보안 설정"
    echo "5. 프로젝트 배포"
    echo ""
    
    read -p "계속 진행하시겠습니까? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "배포가 취소되었습니다."
        exit 0
    fi
    
    check_system
    install_dependencies
    install_docker
    
    echo ""
    echo "=================================================="
    log_success "🎉 기본 설정 완료!"
    echo "=================================================="
    echo ""
    echo "📋 다음 단계:"
    echo "1. 로그아웃 후 다시 로그인 (Docker 그룹 적용)"
    echo "2. 프로젝트 클론: git clone https://github.com/LETUED/crypto-trader-bot.git"
    echo "3. 환경변수 설정: cp .env.docker .env && nano .env"
    echo "4. Docker 실행: docker-compose up -d"
    echo ""
}

# 스크립트 실행
main "$@"