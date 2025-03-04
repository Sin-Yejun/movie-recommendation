from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
import faiss
import numpy as np
from openai import OpenAI
import json
import pandas as pd
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# 🔹 CORS 설정 추가 (보안 설정 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 특정 도메인만 허용 가능 (예: ["http://localhost:3000"])
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST 등)
    allow_headers=["*"],
)

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


class QueryModel(BaseModel):
    query: str


def query_embedding(text):
    """입력 텍스트를 임베딩 벡터로 변환"""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )

    embedding = np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)
    return embedding


def generate_ai_response(query, movie_data):
    """ChatGPT API를 이용해 영화 추천 및 정보 제공"""
    prompt = f"""
    사용자의 질문: "{query}"
    
    아래 영화 데이터와 리뷰를 참고하여, 가장 적절한 답변을 만들어줘.
    
    영화 데이터:
    {json.dumps(movie_data, ensure_ascii=False, indent=2)}

    답변 형식:
    - Markdown 문법을 사용하여 가독성을 높여야 함
    - 필요하면 **볼드체**, *이탤릭체*, 리스트, 제목을 활용
    - 질문의 의도를 분석하여 사용자 친화적인 답변 제공
    - 필요하면 영화 1~3개 추천, 줄거리 요약, 리뷰 요약 등을 포함
    - 답변을 자연스럽게 정리
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content.strip()


@app.post("/chat")
async def search(query_data: QueryModel):
    query = query_data.query
    print(f"사용자 입력: {query}")

    try:
        # FAISS 검색 (상위 5개 영화 찾기)
        embedding = query_embedding(query)
        distances, indices = index.search(embedding, 5)

        if len(indices[0]) == 0:
            raise HTTPException(status_code=404, detail="관련된 영화를 찾을 수 없습니다.")

        # 영화 정보 수집
        relevant_movies = []
        for idx in indices[0]:
            if idx >= len(movies):  # 인덱스 범위 초과 방지
                continue
            movie_data = movies[idx].copy()  # 원본 변경 방지
            movie_data.pop("영화포스터", None)  # 🔹 '영화포스터' 키 제거
            relevant_movies.append(movie_data)

        # AI가 최적의 답변 생성
        response_text = generate_ai_response(query, relevant_movies)
        print(response_text)

        return {"response": response_text}

    except Exception as e:
        print("에러 발생:", str(e))
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")
