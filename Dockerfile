# Dockerfile

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --fix-missing \
    curl \
    unzip \
    chromium-driver \
    git \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# wait-for-it.sh 복사 및 실행 권한 부여
COPY wait-for-it.sh .
RUN chmod +x wait-for-it.sh

COPY . .

ENV PYTHONUNBUFFERED=1

# CMD: 셀레니움 준비되면 wait-for-it.sh 스크립트로 크롤링 실행
CMD ["./wait-for-it.sh"]
