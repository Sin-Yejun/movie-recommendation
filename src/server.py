from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from openai import OpenAI
from fastapi.middleware.cors import CORSMiddleware
import faiss
import numpy as np
import json
import os
import uvicorn
import random

# FastAPI 앱 초기화
app = FastAPI()

# CORS 설정 추가 (보안 설정 가능)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_key = os.getenv("OPENAI_API_KEY")

# OpenAI API 클라이언트
client = OpenAI(api_key = api_key)

# 현재 파일의 디렉토리 경로
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# FAISS 인덱스 불러오기
index = faiss.read_index(os.path.join(BASE_DIR, "db/movie_index.faiss"))

# JSON 영화 정보 불러오기
with open(os.path.join(BASE_DIR, "db/movies.json"), "r", encoding="utf-8") as f:
    movies = json.load(f)

# NumPy 배열로 저장된 영화 리뷰 데이터 불러오기
movie_reviews = np.load(os.path.join(BASE_DIR, "db/movie_reviews.npy"), allow_pickle=True)

# 요청 데이터 모델 정의
class QueryModel(BaseModel):
    query: str

# 입력 텍스트를 OpenAI 임베딩 벡터로 변환
def query_embedding(text):    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)


# 그룹별 리뷰 데이터만 반환
def get_movie_reviews(movie_title, max_length=500):
    reviews = movie_reviews[movie_reviews[:, 0] == movie_title]
    if len(reviews) == 0:
        return {"movie": movie_title, "reviews": {"top": [], "mid": [], "low": []}}

    sorted_reviews = sorted(reviews, key=lambda x: float(x[2]), reverse=True)
    total_reviews = len(sorted_reviews)

    top = sorted_reviews[:total_reviews // 3]
    mid = sorted_reviews[total_reviews // 3: 2 * total_reviews // 3]
    low = sorted_reviews[2 * total_reviews // 3:]

    def extract(group):
        return [
            {
                "author": row[1],
                "rating": float(row[2]),
                "comment": row[3][:max_length] + "..." if len(row[3]) > max_length else row[3]
            }
            for row in group
        ]

    return {
        "movie": movie_title,
        "reviews": {
            "top": extract(top),
            "mid": extract(mid),
            "low": extract(low)
        }
    }

def summarize_reviews_group(group_reviews, label):
    review_text = "\n\n".join(
        f"- 평점: {review['rating']}, 내용: {review['comment']}" for review in group_reviews
    )

    prompt = f"""
    다음은 '{label}' 그룹에 해당하는 영화 리뷰 목록입니다. 이 리뷰들을 종합해 간결하게 요약해줘. 핵심 내용, 공통 의견, 인상적인 문구 등을 중심으로 작성하되, 길지 않게 정리해줘.

    리뷰 목록:
    {review_text}

    요약:
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

# ChatGPT API를 이용해 영화 추천 및 리뷰 요약 생성
def generate_ai_response(query, movie_data, reviews):
    prompt = f"""
    사용자의 질문: "{query}"

    아래 영화 데이터와 리뷰를 참고하여, 가장 적절한 답변을 만들어줘.

    영화 정보:
    {json.dumps(movie_data, ensure_ascii=False, indent=2)}

    영화 리뷰:
    {reviews}

    답변 형식:
    - Markdown 문법을 사용하여 가독성을 높여야 함.
    - 필요하면 **볼드체**, *이탤릭체*, 리스트, 제목을 활용.
    - 질문의 의도를 분석하여 사용자 친화적인 답변 제공.
    - 필요하면 영화 추천, 줄거리 요약, 리뷰 요약 등을 포함.
    - 답변을 자연스럽게 정리.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    print(prompt)
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content


@app.post("/chat")
async def search(query_data: QueryModel):
    query = query_data.query
    print(f"사용자 입력: {query}")

    try:
        # FAISS 검색 (상위 5개 영화 찾기)
        embedding = query_embedding(query)
        distances, indices = index.search(embedding, 3)

        if len(indices[0]) == 0:
            raise HTTPException(status_code=404, detail="관련된 영화를 찾을 수 없습니다.")

        # 영화 정보 및 리뷰 데이터 수집
        relevant_movies = []
        summarized_reviews = []
        for idx in indices[0]:
            if idx >= len(movies):  # 인덱스 범위 초과 방지
                continue
            movie_data = movies[idx].copy()
            movie_data.pop("영화포스터", None)  # 포스터 제거
            relevant_movies.append(movie_data)

            # 해당 영화의 리뷰 가져오기
            raw_reviews = get_movie_reviews(movie_data["제목"])
            top_summary = summarize_reviews_group(raw_reviews["reviews"]["top"], "상위")
            mid_summary = summarize_reviews_group(raw_reviews["reviews"]["mid"], "중위")
            low_summary = summarize_reviews_group(raw_reviews["reviews"]["low"], "하위")

            summarized_reviews.append({
                "movie": raw_reviews["movie"],
                "summaries": {
                    "top": top_summary,
                    "mid": mid_summary,
                    "low": low_summary
                }
            })
        # 리뷰를 JSON 배열로 변환
        reviews_json = json.dumps(summarized_reviews, ensure_ascii=False, indent=2)

        # AI가 답변 생성
        response_text = generate_ai_response(query, relevant_movies, reviews_json)
        print(response_text)

        return StreamingResponse(response_text, media_type="text/plain")

    except Exception as e:
        print("에러 발생:", str(e))
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")



# 루트 경로 추가 (배포 시 상태 체크 가능)
@app.get("/")
async def root():
    return {"message": "서버가 정상적으로 실행 중입니다!"}


# 배포 환경에 맞게 실행 설정
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))  # Render에서 자동 감지
    uvicorn.run(app, host="0.0.0.0", port=port)
