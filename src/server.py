from fastapi import FastAPI
import faiss
import numpy as np
from openai import OpenAI
import json
import pandas as pd

app = FastAPI()

# OpenAI API 클라이언트
client = OpenAI()

# FAISS 인덱스 불러오기
index = faiss.read_index("db/movie_index.faiss")
movie_titles = np.load("db/movie_titles.npy")

# JSON 영화 정보 불러오기
with open("db/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

# CSV 리뷰 데이터 불러오기
df = pd.read_csv("db/movie_reviews.csv", encoding="utf-8")


def query_embedding(text):
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    embedding = np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)  # ✅ 2차원 배열로 변환

    return embedding


# 🔹 AI가 JSON & CSV를 분석하여 최적의 답변을 생성
def generate_ai_response(query, movie_data):
    prompt = f"""
    사용자의 질문: "{query}"
    
    아래 영화 데이터와 리뷰를 참고하여, 가장 적절한 답변을 만들어줘.
    
    영화 데이터:
    {movie_data}

    답변 형식:
    - 질문의 의도를 분석하여 사용자 친화적인 답변 제공
    - 필요하면 영화 1~3개 추천, 줄거리 요약, 리뷰 요약 등을 포함
    - 답변을 자연스럽게 정리

    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()

# 🔹 AI가 JSON 데이터를 검색하여 답변 생성
@app.get("/chat")
async def search(query: str):
    print(f"사용자 입력: {query}")

    # FAISS 검색 (상위 5개 영화 찾기)
    embedding = query_embedding(query)
    distances, indices = index.search(embedding, 5)

    # 영화 정보 수집
    relevant_movies = []
    for idx in indices[0]:
        relevant_movies.append(movies[idx])

    # AI가 최적의 답변 생성
    response_text = generate_ai_response(query, relevant_movies)
    print(response_text)
    return response_text
