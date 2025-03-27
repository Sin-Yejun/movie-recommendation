# === 빌드 단계 ===
FROM python:3.10-slim AS builder

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
FROM python:3.10-slim

WORKDIR /app

# 실행 단계에 꼭 필요한 것만 설치
RUN apt-get update && apt-get install -y --fix-missing \
    curl \
    unzip \
    chromium-driver \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# builder 단계에서 설치된 python 패키지 복사
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# wait-for-it.sh 복사 및 실행 권한 부여
COPY wait-for-it.sh .
RUN chmod +x wait-for-it.sh

COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["./wait-for-it.sh"]
