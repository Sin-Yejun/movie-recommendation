# === 빌드 단계 ===
# === 빌드 단계 ===
# Slim 이미지 대신 일반 이미지를 사용하여 의존성 문제 해결 시도
FROM python:3.10 AS builder

WORKDIR /app

# 필수 빌드도구 설치 (임시)
RUN apt-get update && apt-get install -y --fix-missing \
    build-essential \
    curl \
    unzip \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# === 실행 단계 ===
FROM python:3.10

WORKDIR /app

# 실행 단계에 꼭 필요한 것만 설치
RUN apt-get update && apt-get install -y --fix-missing \
    curl \
    unzip \
    chromium-driver \
    git \
    libgomp1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# builder 단계에서 설치된 python 패키지 복사
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# wait-for-it.sh 복사 및 실행 권한 부여
COPY wait-for-it.sh .
RUN chmod 755 wait-for-it.sh

COPY . .

ENV PYTHONUNBUFFERED=1

# Cloud Run에서는 wait-for-it 불필요 (단일 컨테이너)
# CMD ["./wait-for-it.sh"]

# 직접 포트 8080으로 실행 (Cloud Run의 $PORT 환경변수 사용)
# sh -c를 사용하여 환경변수 $PORT를 쉘에서 확장하도록 함 (기본값 8080)
CMD ["sh", "-c", "uvicorn src.server:app --host 0.0.0.0 --port ${PORT:-8080}"]
