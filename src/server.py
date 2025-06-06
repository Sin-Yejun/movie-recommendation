import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import faiss
import numpy as np
import json
import uvicorn
import random

# 환경설정
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# FastAPI 앱 초기화
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

index = faiss.read_index(os.path.join(BASE_DIR, "db/movie_index.faiss"))
with open(os.path.join(BASE_DIR, "db/movies.json"), "r", encoding="utf-8") as f:
    movies = json.load(f)
movie_reviews = np.load(os.path.join(BASE_DIR, "db/movie_reviews.npy"), allow_pickle=True)
movie_titles = [movie["제목"] for movie in movies if "제목" in movie]

class QueryModel(BaseModel):
    query: str

class MovieTitleExtraction(BaseModel):
    titles: list[str] = Field(
        description="질문에서 언급된 영화의 정확한 제목 리스트. 없다면 반드시 ['추천']으로 반환."
    )

def extract_movie_titles_ai(query, movie_titles):
    system_msg = (
        "너는 영화 제목 추출 전문가야. 사용자의 질문에서 언급하거나 암시적으로 표현한 영화명을 "
        "아래 영화 데이터 목록에서 최대한 의도를 파악해서, 반드시 영화 데이터에 포함된 제목과 똑같이 리스트로 반환해. "
        "질문에 영화 제목이 없다면 반드시 ['추천']만 반환해. "
        "반환 형식은 반드시 JSON이고, 키는 'titles'야."
        "\n\n---답변 예시---"
        "\n질문: 마크 영화 재밌어?"
        "\n답변: {\"titles\": [\"A MINECRAFT MOVIE 마인크래프트 무비\"]}"
        "\n질문: 야당이랑 미션 임파서블 중 뭐가 더 재밌나"
        "\n답변: {\"titles\": [\"야당\", \"미션 임파서블: 데드 레코닝\"]}"
        "\n질문: 요즘 볼만한 거 추천해줘"
        "\n답변: {\"titles\": [\"추천\"]}"
        f"\n\n영화 데이터: {movie_titles}"
    )
    user_msg = (
        f"질문: {query}\n\n"
        "질문에 언급된 영화 제목을 반드시 위 데이터와 완전히 동일한 표기로만 골라, JSON의 'titles' 키의 리스트로 반환해. "
        "없으면 반드시 ['추천']만 반환해."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg}
        ],
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content
    try:
        titles = json.loads(content)["titles"]
        return titles
    except Exception:
        return ["추천"]

# -- 임베딩 함수 등은 동일 --
def query_embedding(text):    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)

def get_balanced_movie_reviews(movie_title, max_per_group=10, max_length=500):
    reviews = movie_reviews[movie_reviews[:, 0] == movie_title]
    if len(reviews) == 0:
        return {"movie": movie_title, "reviews": {"low": [], "mid": [], "top": []}}
    def filter_by_score(min_score, max_score):
        return [r for r in reviews if min_score <= float(r[2]) <= max_score]
    def sample_and_format(group):
        sampled = random.sample(group, min(len(group), max_per_group))
        return [
            {
                "author": row[1],
                "rating": float(row[2]),
                "comment": str(row[3])[:max_length] + "..." if len(str(row[3])) > max_length else str(row[3])
            }
            for row in sampled
        ]
    low_group = filter_by_score(1.0, 3.0)
    mid_group = filter_by_score(4.0, 7.0)
    high_group = filter_by_score(8.0, 10.0)
    return {
        "movie": movie_title,
        "reviews": {
            "low": sample_and_format(low_group),
            "mid": sample_and_format(mid_group),
            "top": sample_and_format(high_group)
        }
    }

def summarize_reviews_group(group_reviews, label):
    if not group_reviews:
        return f"'{label}' 그룹에는 요약할 리뷰가 충분하지 않습니다."
    review_text = "\n\n".join(
        f"- 평점: {review['rating']}, 내용: {review['comment']}" for review in group_reviews
    )
    if label == "상위 (평점 8~10점)":
        style_instruction = "이 리뷰들은 대부분 긍정적입니다. 영화의 강점, 칭찬받는 부분, 인상 깊은 표현 위주로 짧게 요약해줘."
    elif label == "중위 (평점 4~7점)":
        style_instruction = "이 리뷰들은 긍정과 부정이 섞여 있을 수 있습니다. 관객들의 엇갈린 평가나 의견 차이 위주로 짧게 요약해줘."
    elif label == "하위 (평점 1~3점)":
        style_instruction = "이 리뷰들은 부정적인 의견이 많습니다. 비판적 시선, 문제점, 실망한 이유를 위주로 짧게 요약해줘."
    prompt = f"""
    다음은 리뷰 '{label}' 그룹에 해당하는 영화 리뷰 목록입니다. {style_instruction}

    리뷰 목록:
    {review_text}

    요약:
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content.strip()

def generate_ai_response(query, movie_data, reviews=None, is_general_recommend=False):
    if is_general_recommend:
        prompt = f"""
        사용자의 질문: "{query}"

        주어진 영화 데이터는 이미 개봉한 영화들에 대한 정보야.
        아래 영화 데이터만 참고해서, 사용자에게 어울릴 만한 영화를 추천해줘.
        사용자가 아래 영화 데이터에 없는 영화를 말하면 최신 영화만 추천 가능하다고 말하고 다른 걸 추천해줘.
        ex) 최신 영화가 아닌 영화에 대한 설명은 어렵습니다. 대신 최신 영화를 아래와 같이 추천해 드리겠습니다.

        - 영화별로 제목, 장르, 간단한 줄거리, 추천 포인트를 적어줘.
        - 관객수, 평점, 급상승 순위 등을 참고하고 전체적인 인상과 특징 위주로 알려줘.
        - 답변은 Markdown 문법(볼드, 리스트 등)으로 읽기 쉽게 해줘.
        - 이모티콘을 섞어서 가독성을 높여도 좋아.

        영화 정보:
        {json.dumps(movie_data, ensure_ascii=False, indent=2)}
        """
    else:
        prompt = f"""
        사용자의 질문: "{query}"

        주어진 영화 데이터는 이미 개봉한 영화들에 대한 정보야.
        아래 영화 데이터와 리뷰 요약(상위/중위/하위)을 참고해서, 질문 영화에 대해 상세하고 친절한 답변을 만들어줘.

        - 영화 줄거리, 장르, 상/중/하 리뷰 요약(특징/호불호/불만 모두) 중심으로 안내해줘.
        - 관람 전 알아두면 좋을 포인트나, 관객의 인상적인 반응도 자연스럽게 포함해줘.
        - 필요하면 비슷한 분위기의 영화 한두 편 추천해도 좋아.
        - 답변은 Markdown 문법(제목, 리스트, 강조 등)을 적극 활용해줘.
        - 이모티콘을 섞어서 가독성을 높여도 좋아.

        영화 정보:
        {json.dumps(movie_data, ensure_ascii=False, indent=2)}

        영화 리뷰 요약:
        {reviews}
        """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        stream=True
    )
    print("[답변 프롬프트]", prompt)
    for chunk in response:
        if chunk.choices and chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

@app.post("/chat")
async def search(query_data: QueryModel):
    query = query_data.query
    print(f"사용자 입력: {query}")

    # === 영화 제목 추출 ===
    extracted_titles = extract_movie_titles_ai(query, movie_titles)
    print("extracted_titles:", extracted_titles)

    is_general_recommend = (extracted_titles == ['추천'])

    try:
        # 임베딩 및 FAISS 검색은 추천 질문일 때도 전체적으로 하길 원하면 유지
        embedding = query_embedding(query)
        distances, indices = index.search(embedding, 5)

        relevant_movies = []
        summarized_reviews = []
        # (1) 추천 질문인 경우: 상위 3개 영화 전체정보를 프롬프트에
        if is_general_recommend:
            for idx in indices[0]:
                if idx >= len(movies): continue
                movie_data = movies[idx].copy()
                movie_data.pop("영화포스터", None)
                relevant_movies.append(movie_data)
            response_text = generate_ai_response(query, relevant_movies, reviews=None, is_general_recommend=True)

        # (2) 특정 영화 질문: 추출된 제목 각각에 대해 리뷰 요약
        else:
            for title in extracted_titles:
                try:
                    idx = movie_titles.index(title)
                except ValueError:
                    continue  # 못찾으면 skip
                movie_data = movies[idx].copy()
                movie_data.pop("영화포스터", None)
                relevant_movies.append(movie_data)

                raw_reviews = get_balanced_movie_reviews(title)
                top_summary = summarize_reviews_group(raw_reviews["reviews"]["top"], "상위 (평점 8~10점)")
                mid_summary = summarize_reviews_group(raw_reviews["reviews"]["mid"], "중위 (평점 4~7점)")
                low_summary = summarize_reviews_group(raw_reviews["reviews"]["low"], "하위 (평점 1~3점)")

                summarized_reviews.append({
                    "movie": title,
                    "summaries": {
                        "top": top_summary,
                        "mid": mid_summary,
                        "low": low_summary
                    }
                })
            reviews_json = json.dumps(summarized_reviews, ensure_ascii=False, indent=2)
            response_text = generate_ai_response(query, relevant_movies, reviews_json, is_general_recommend=False)

        return StreamingResponse(response_text, media_type="text/plain")

    except Exception as e:
        print("에러 발생:", str(e))
        raise HTTPException(status_code=500, detail="서버 오류가 발생했습니다.")


@app.get("/")
async def root():
    return {"message": "서버가 정상적으로 실행 중입니다!"}


def test_single_query(query):
    print(f"\n[Q] 질문: {query}")

    # 1. 제목 추출
    extracted_titles = extract_movie_titles_ai(query, movie_titles)
    print("  >> 추출된 제목:", extracted_titles)

    is_general_recommend = (extracted_titles == ['추천'])
    print("  >> 추천 질문 여부:", is_general_recommend)

    # 2. 추천 분기
    if is_general_recommend:
        embedding = query_embedding(query)
        distances, indices = index.search(embedding, 5)
        relevant_movies = []
        for idx in indices[0]:
            if idx >= len(movies): continue
            movie_data = movies[idx].copy()
            movie_data.pop("영화포스터", None)
            relevant_movies.append(movie_data)
        response_gen = generate_ai_response(query, relevant_movies, reviews=None, is_general_recommend=True)
    else:
        relevant_movies = []
        summarized_reviews = []
        for title in extracted_titles:
            try:
                idx = movie_titles.index(title)
            except ValueError:
                continue
            movie_data = movies[idx].copy()
            movie_data.pop("영화포스터", None)
            relevant_movies.append(movie_data)
            raw_reviews = get_balanced_movie_reviews(title)
            top_summary = summarize_reviews_group(raw_reviews["reviews"]["top"], "상위 (평점 8~10점)")
            mid_summary = summarize_reviews_group(raw_reviews["reviews"]["mid"], "중위 (평점 4~7점)")
            low_summary = summarize_reviews_group(raw_reviews["reviews"]["low"], "하위 (평점 1~3점)")
            summarized_reviews.append({
                "movie": title,
                "summaries": {
                    "top": top_summary,
                    "mid": mid_summary,
                    "low": low_summary
                }
            })
        reviews_json = json.dumps(summarized_reviews, ensure_ascii=False, indent=2)
        response_gen = generate_ai_response(query, relevant_movies, reviews_json, is_general_recommend=False)

    # 3. 답변 출력
    print("[A] 답변:")
    answer = ""
    try:
        for chunk in response_gen:
            answer += chunk
        print(answer.strip())
    except Exception as e:
        print("  >> 오류:", e)

if __name__ == "__main__":
    # while True:
    #     q = input("질문 입력 (엔터 시 종료): ").strip()
    #     if not q:
    #         break
    #     test_single_query(q)
    port = int(os.getenv("PORT", 8000))  # Render에서 자동 감지
    uvicorn.run(app, host="0.0.0.0", port=port)