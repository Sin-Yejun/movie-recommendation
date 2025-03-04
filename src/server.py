from fastapi import FastAPI
import faiss
import numpy as np
from  openai import OpenAI
import json
import pandas as pd

app = FastAPI()

# OpenAI API 키 설정
client = OpenAI()

# FAISS 인덱스 불러오기
index = faiss.read_index("db/movie_index.faiss")
movie_titles = np.load("db/movie_titles.npy")

# JSON 영화 정보 불러오기
with open("db/movies.json", "r", encoding="utf-8") as f:
    movies = json.load(f)

# CSV 리뷰 데이터 불러오기
df = pd.read_csv("db/movie_reviews.csv", encoding="utf-8")

# 질문 유형 판별 함수 (ChatGPT API 이용)
def classify_query(user_input):
    prompt = f"""
    다음 사용자의 질문을 분석해서 영화 추천이면 "recommend"를, 
    특정 영화의 정보를 묻는 질문이면 "info"를 출력해줘.

    질문: "{user_input}"
    답변 형식: "recommend" 또는 "info" 만 출력.

    예제:
    "SF 영화 추천해줘" → recommend
    "미키 17 개봉일 언제야?" → info
    "요즘 재밌는 영화 있어?" → recommend
    "캡틴 아메리카 출연진 알려줘" → info
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],

    )
    return response.choices[0].message.strip()

# 영화 정보 검색 함수 (JSON에서 찾기)
def get_movie_info(title, field):
    for movie in movies:
        if title in movie["제목"]:
            return movie.get(field, "해당 정보 없음")
    return "영화를 찾을 수 없음"

# 사용자 입력을 임베딩으로 변환하는 함수
def query_embedding(text):
    response = client.Embedding.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)


# 추천 API
@app.get("/chat")
async def search(query: str):
    query_type = classify_query(query)  # 질문 유형 판별

    if query_type == "recommend":
        # 추천 영화 찾기 (FAISS 사용)
        embedding = query_embedding(query)
        distances, indices = index.search(embedding, 3)
        recommended_movies = [movie_titles[i] for i in indices[0]]
        return {"유형": "recommend", "추천 영화": recommended_movies}

    elif query_type == "info":
        # 개별 영화 정보 찾기
        for movie in movies:
            if movie["제목"] in query:
                # 사용자가 원하는 정보 필드 찾기
                if "개봉" in query:
                    field = "개봉일"
                elif "출연진" in query:
                    field = "출연진"
                elif "상영 시간" in query:
                    field = "상영 시간"
                elif "평점" in query:
                    field = "관람객 평점"
                else:
                    return {"유형": "info", "결과": "어떤 정보를 원하는지 모르겠어요."}

                return {"유형": "info", "영화": movie["제목"], "정보": get_movie_info(movie["제목"], field)}

    return {"유형": "error", "결과": "질문을 이해하지 못했어요."}

# uvicorn server:app --reload
