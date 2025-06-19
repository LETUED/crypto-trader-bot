# 🛠️ 설치 가이드

## 시스템 요구사항

- Python 3.8 이상
- pip 패키지 관리자
- Git (선택사항)

## 1. 기본 설치

### 가상환경 생성 및 활성화
```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 기본 패키지 설치
```bash
# pip 업그레이드
pip install --upgrade pip

# 기본 패키지 설치
pip install -r requirements.txt
```

## 2. TA-Lib 설치 (중요)

TA-Lib은 technical analysis(기술적 분석) library(라이브러리)로 별도의 시스템 dependency(의존성)가 필요합니다.

### macOS
```bash
# Homebrew 사용
brew install ta-lib

# 또는 MacPorts 사용
sudo port install ta-lib
```

### Ubuntu/Debian
```bash
# 시스템 패키지 설치
sudo apt-get update
sudo apt-get install build-essential
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
```

### Windows
```bash
# conda 사용 (권장)
conda install -c conda-forge ta-lib

# 또는 미리 컴파일된 wheel 사용
pip install TA-Lib
```

### TA-Lib 설치 확인
```python
python -c "import talib; print('TA-Lib 설치 성공!')"
```

## 3. 패키지별 설치 문제 해결

### 일반적인 문제들

#### 1. telegram-bot 패키지 오류
```bash
# 잘못된 패키지명
pip install telegram-bot  # ❌

# 올바른 패키지명
pip install python-telegram-bot  # ✅
```

#### 2. freqtrade 설치 오류
```bash
# 최신 버전으로 설치
pip install freqtrade[all]

# 특정 버전 설치
pip install freqtrade==2023.12
```

#### 3. ccxt 설치 오류
```bash
# 최신 버전 설치
pip install ccxt

# 개발 버전 설치 (최신 거래소 지원)
pip install git+https://github.com/ccxt/ccxt.git
```

#### 4. pandas/numpy 호환성 문제
```bash
# 호환 가능한 버전으로 다운그레이드
pip install pandas==1.5.3 numpy==1.21.6
```

#### 5. Pydantic v2 관련 문제
```bash
# BaseSettings 관련 오류 발생시
pip install pydantic-settings

# 또는 전체 재설치
pip uninstall pydantic pydantic-settings
pip install pydantic>=2.0.0 pydantic-settings>=2.0.0
```

## 4. 단계별 설치 (문제 발생시)

문제가 발생하면 다음 순서로 설치를 진행하세요:

### Step 1: 핵심 패키지
```bash
pip install numpy pandas
```

### Step 2: TA-Lib 설치
```bash
# 시스템에 맞는 방법으로 TA-Lib 설치 후
pip install TA-Lib
```

### Step 3: 거래 관련 패키지
```bash
pip install ccxt freqtrade
```

### Step 4: 웹 프레임워크
```bash
pip install fastapi uvicorn
```

### Step 5: 기타 패키지
```bash
pip install python-telegram-bot structlog pydantic python-dotenv
```

### Step 6: 개발 도구
```bash
pip install pytest black isort mypy
```

## 5. 설치 검증

모든 패키지가 올바르게 설치되었는지 확인:

```bash
# 시스템 검증 실행
python main.py validate

# 또는 개별 패키지 확인
python -c "
import freqtrade
import ccxt
import pandas
import numpy
import talib
import telegram
print('✅ 모든 핵심 패키지 설치 완료!')
"
```

## 6. 문제 해결

### 일반적인 오류 메시지와 해결책

#### "Microsoft Visual C++ 14.0 is required" (Windows)
```bash
# Visual Studio Build Tools 설치
# https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

#### "error: ta-lib/ta_defs.h: No such file or directory"
```bash
# TA-Lib C 라이브러리가 설치되지 않음
# 위의 TA-Lib 설치 섹션 참조
```

#### "No module named '_ta_lib'"
```bash
# TA-Lib Python wrapper 재설치
pip uninstall TA-Lib
pip install TA-Lib
```

#### 메모리 부족 오류
```bash
# swap 파일 생성 (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

## 7. Docker를 이용한 설치 (권장)

복잡한 dependency(의존성) 문제를 피하고 싶다면 Docker 사용을 권장합니다:

```dockerfile
# Dockerfile 예시
FROM python:3.9-slim

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

# TA-Lib 설치
RUN wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz && \
    tar -xzf ta-lib-0.4.0-src.tar.gz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && make install && \
    cd .. && rm -rf ta-lib*

# Python 패키지 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 애플리케이션 복사
COPY . /app
WORKDIR /app

CMD ["python", "main.py", "validate"]
```

## 8. 성능 최적화

### 선택적 패키지 설치
```bash
# 백테스트만 사용하는 경우
pip install freqtrade[plot]

# 실시간 거래만 사용하는 경우  
pip install freqtrade[live]

# 모든 기능 사용
pip install freqtrade[all]
```

### 빠른 수치 연산을 위한 패키지
```bash
pip install numba  # JIT 컴파일러
pip install bottleneck  # 빠른 numpy 연산
```

## 9. 개발 환경 설정

### 코드 품질 도구
```bash
# 코드 포맷팅
pip install black isort

# 타입 체킹
pip install mypy

# 린팅
pip install flake8

# 보안 검사
pip install bandit
```

### IDE 설정
- **VS Code**: Python extension 설치
- **PyCharm**: 가상환경을 프로젝트 인터프리터로 설정
- **Jupyter**: `pip install jupyter` 후 노트북 환경에서 분석

## 10. 설치 완료 확인

```bash
# 전체 시스템 테스트
python main.py validate

# 전략 테스트
python -c "from strategies.rsi_strategy import test_rsi_strategy; test_rsi_strategy()"

# 단위 테스트 실행
pytest tests/ -v
```

설치가 완료되면 `python main.py --help` 명령으로 사용 가능한 옵션들을 확인할 수 있습니다.

---

**💡 팁**: 설치 중 문제가 발생하면 각 단계를 개별적으로 실행하고, 오류 메시지를 자세히 읽어보세요. 대부분의 문제는 system dependency(시스템 의존성) 누락이나 version(버전) 충돌입니다.