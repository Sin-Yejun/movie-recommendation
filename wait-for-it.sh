#!/bin/bash

# selenium이 뜰 때까지 대기
until curl -s http://selenium:4444/wd/hub/status | grep -q "ready"; do
  echo "Waiting for Selenium..."
  sleep 2
done

echo "Selenium is ready! Starting crawl..."

# 크롤링 3단계 순서대로 실행
python src/영화정보크롤링.py
python src/영화리뷰크롤링.py
OPENAI_API_KEY=$OPENAI_API_KEY python src/create_embedding.py

# GitHub에 푸시
git config --global user.name "Sin-Yejun"
git config --global user.email "21900402@handong.ac.kr"
git remote set-url origin https://x-access-token:${GH_PAT}@github.com/Sin-Yejun/movie-recommendation.git
git add .
git commit -m "자동 크롤링 및 임베딩 업데이트" || echo "No changes to commit"
git push
