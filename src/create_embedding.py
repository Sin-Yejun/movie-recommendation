from openai import OpenAI
import faiss
import numpy as np
import pandas as pd
import json
import os
import pickle
import hashlib
from datetime import datetime
from collections import Counter
import re
from dotenv import load_dotenv
load_dotenv()
# OpenAI API 클라이언트
client = OpenAI()

# 캐시 파일 경로
CACHE_FILE = "src/db/embedding_cache.pkl"

# 캐시 로드
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "rb") as f:
        embedding_cache = pickle.load(f)
    print(f"임베딩 캐시 로드 완료: {len(embedding_cache)}개")
else:
    embedding_cache = {}
    print("새로운 임베딩 캐시 생성")

# OpenAI 임베딩 함수 (캐시 적용)
def get_embedding(text):
    # 텍스트의 해시값 생성 (고유 키)
    text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
    
    if text_hash in embedding_cache:
        return embedding_cache[text_hash]
    
    # API 호출
    try:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=text,
        )
        embedding = response.data[0].embedding
        embedding_cache[text_hash] = embedding # 캐시에 저장
        return embedding
    except Exception as e:
        print(f"임베딩 생성 실패: {e}")
        return [0.0] * 1536 # 실패 시 0벡터 반환 (에러 방지)

# 불용어 리스트 (간단 버전)
STOP_WORDS = set([
    "영화", "관람객", "점", "너무", "진짜", "정말", "보고", "있는", "하는", "그리고", "많이", 
    "그냥", "좀", "잘", "더", "수", "게", "거", "것", "들", "이", "가", "을", "를", "은", "는",
    "에", "의", "와", "과", "도", "다", "로", "으로", "만", "서", "에서", "하다", "있다"
])

def extract_keywords(reviews, top_n=10):
    if not reviews:
        return ""
    
    words = []
    for review in reviews:
        # 한글, 영어만 남기고 제거
        cleaned = re.sub(r'[^가-힣a-zA-Z\s]', '', str(review))
        tokens = cleaned.split()
        for token in tokens:
            if len(token) > 1 and token not in STOP_WORDS:
                words.append(token)
    
    counter = Counter(words)
    top_keywords = [word for word, count in counter.most_common(top_n)]
    return ", ".join(top_keywords)

# JSON 영화 정보 불러오기
with open("src/db/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

# CSV 리뷰 데이터 불러오기
if os.path.exists("src/db/movie_reviews.csv"):
    df = pd.read_csv("src/db/movie_reviews.csv", encoding="utf-8")
    # CSV 리뷰 데이터를 NumPy 배열로 저장 (빠른 로드 가능)
    np.save("src/db/movie_reviews.npy", df.to_numpy(), allow_pickle=True)
    
    # 영화별 리뷰 그룹화 (Dictionary로 변환)
    reviews_by_title = df.groupby('제목')['리뷰'].apply(list).to_dict()
else:
    print("리뷰 데이터 파일이 없습니다.")
    np.save("src/db/movie_reviews.npy", np.array([]), allow_pickle=True)
    reviews_by_title = {}


# 영화별 임베딩 생성
movie_texts = []
print("임베딩 텍스트 생성 중...")
for m in movies:
    title = m['제목']
    genre = m['장르']
    plot = m['줄거리']
    
    # 리뷰 키워드 추출
    reviews = reviews_by_title.get(title, [])
    keywords = extract_keywords(reviews)
    
    # 임베딩 텍스트 구성: 제목 + 장르 + 줄거리 + [리뷰 키워드]
    text = f"제목: {title}\n장르: {genre}\n줄거리: {plot}\n관객 키워드: {keywords}"
    movie_texts.append(text)
    # print(f"[{title}] 키워드: {keywords}") # 디버깅용

print("임베딩 생성 시작...")
movie_embeddings_list = []
for text in movie_texts:
    emb = get_embedding(text)
    movie_embeddings_list.append(emb)

movie_embeddings = np.array(movie_embeddings_list, dtype=np.float32)

# 캐시 저장
with open(CACHE_FILE, "wb") as f:
    pickle.dump(embedding_cache, f)
print("임베딩 캐시 저장 완료.")

# FAISS 인덱스 생성 (1536차원, cosine similarity)
index = faiss.IndexFlatL2(1536)  # OpenAI 임베딩은 1536차원
index.add(movie_embeddings)

# 영화 검색용 FAISS 저장
faiss.write_index(index, "src/db/movie_index.faiss")
print(f"FAISS 인덱스 저장 완료. 총 {len(movies)}개 영화.")

# 현재 날짜를 today.txt에 저장
current_date = datetime.now().strftime("%Y-%m-%d")
with open("src/db/date.txt", "w", encoding="utf-8") as f:
    f.write(current_date + " 영화 정보 업데이트 완료!")