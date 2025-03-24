# Dockerfile

FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    chromium-driver \
    git \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1

CMD python src/영화정보크롤링.py && \
    python src/영화리뷰크롤링.py && \
    python src/create_embedding.py \
    OPENAI_API_KEY=$OPENAI_API_KEY python src/create_embedding.py && \
    git config --global user.name "Sin-Yejun" && \
    git config --global user.email "21900402@handong.ac.kr" && \
    git remote set-url origin https://x-access-token:${GH_PAT}@github.com/Sin-Yejun/movie-recommendation.git && \
    git add . && \
    git commit -m "자동 크롤링 및 임베딩 업데이트" || echo "No changes to commit" && \
    git push
