from openai import OpenAI
import faiss
import numpy as np
import pandas as pd
import json

api_key = os.getenv("OPENAI_API_KEY")

# OpenAI API 클라이언트
client = OpenAI(api_key = api_key)

# OpenAI 임베딩 함수
def get_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
    )
    return response.data[0].embedding

# JSON 영화 정보 불러오기
with open("src/db/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

# CSV 리뷰 데이터 불러오기
df = pd.read_csv("src/db/movie_reviews.csv", encoding="utf-8")

# 영화별 임베딩 생성
movie_texts = [f"{m['제목']} {m['장르']} {m['줄거리']}" for m in movies]

movie_embeddings = np.array([get_embedding(text) for text in movie_texts], dtype=np.float32)

# FAISS 인덱스 생성 (1536차원, cosine similarity)
index = faiss.IndexFlatL2(1536)  # OpenAI 임베딩은 1536차원
index.add(movie_embeddings)

# 영화 검색용 FAISS 저장
faiss.write_index(index, "src/db/movie_index.faiss")

# CSV 리뷰 데이터를 NumPy 배열로 저장 (빠른 로드 가능)
np.save("src/db/movie_reviews.npy", df.to_numpy(), allow_pickle=True)
