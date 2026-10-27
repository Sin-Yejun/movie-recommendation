import os
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, ValidationError
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import faiss
import numpy as np
import pandas as pd
import io
import urllib.request
import json
from typing import Literal
import uvicorn
import random
from dotenv import load_dotenv
load_dotenv()

# 환경설정
# OpenAI 클라이언트 초기화 (API 키가 없어도 서버가 죽지 않도록 예외 처리)
try:
    client = OpenAI()
except Exception as e:
    print(f"Warning: OpenAI API Key not found. Chat features will not work. Error: {e}")
    client = None

# FastAPI 앱 초기화
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://sin-yejun.github.io",  # 실제 배포된 프론트엔드 주소 (Github Pages)
        "https://movie.yejunsin.dev",   # 서브도메인 
        "http://127.0.0.1:5500",        # 로컬 테스트용
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# [보안 & 비용 절약] API 호출 제한 (Rate Limiting)
import time
from datetime import datetime, date
from fastapi import Request

client_last_request = {}

# === 하루 총 요청 제한 (Global Limit) ===
DAILY_LIMIT = 100 
daily_request_count = 0
last_reset_date = date.today()

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    global daily_request_count, last_reset_date

    # 챗봇 API 요청만 제한 (/chat)
    if request.url.path == "/chat" and request.method == "POST":
        
        # 1. 날짜 변경 체크 (자정 지나면 카운터 리셋)
        today = date.today()
        if today != last_reset_date:
            daily_request_count = 0
            last_reset_date = today
            print(f"🔄 날짜 변경: 카운터가 초기화되었습니다. ({today})")

        # 2. 하루 총량 제한 체크 (Money Saver)
        if daily_request_count >= DAILY_LIMIT:
            print(f"🚫 일일 한도 초과! ({daily_request_count}/{DAILY_LIMIT})")
            resp = StreamingResponse(
                iter([f"죄송합니다. 오늘 서버의 AI 예산({DAILY_LIMIT}회)이 모두 소진되었습니다. 내일 다시 와주세요! 😢"]), 
                media_type="text/plain", 
                status_code=429
            )
            resp.headers["Access-Control-Allow-Origin"] = "*"
            return resp

        # 3. IP별 도배 방지 (2초 쿨타임)
        client_ip = request.client.host
        current_time = time.time()
        
        last_time = client_last_request.get(client_ip, 0)
        
        # 2초 미만 요청 시 차단
        if current_time - last_time < 2:
            resp = StreamingResponse(
                iter(["너무 빨라요! 2초만 쉬었다 질문해주세요. 🐢"]),
                media_type="text/plain",
                status_code=429
            )
            # CORS 헤더 수동 추가 (미들웨어 필터 전이라 필요할 수 있음)
            resp.headers["Access-Control-Allow-Origin"] = "https://sin-yejun.github.io"
            return resp
        
        # 정상 요청 처리: 시간 기록 업데이트
        client_last_request[client_ip] = current_time
        
        # 카운트 증가 (본 게임 시작)
        daily_request_count += 1
        
    response = await call_next(request)
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 데이터는 매일 GitHub Actions가 저장소에 커밋하므로, 재배포 없이 저장소에서 주기적으로 다시 받아온다
DATA_URL = os.getenv("DATA_URL", "https://raw.githubusercontent.com/Sin-Yejun/movie-recommendation/master/src/db")
RELOAD_SECONDS = 3600

index = None
movies = []
movie_reviews = np.array([])
last_loaded = 0.0

def read_data(name):
    try:
        return urllib.request.urlopen(f"{DATA_URL}/{name}", timeout=10).read()
    except Exception as e:
        print(f"⚠️ 원격 {name} 로드 실패, 이미지에 포함된 파일 사용: {e}")
        with open(os.path.join(BASE_DIR, "db", name), "rb") as f:
            return f.read()

def load_data():
    global index, movies, movie_reviews, last_loaded
    last_loaded = time.time()  # 실패해도 매 요청마다 재시도하지 않도록 먼저 갱신
    try:
        # 파일 경로 대신 bytes로 읽어 FAISS의 윈도우 한글 경로 이슈도 피함
        new_index = faiss.deserialize_index(np.frombuffer(read_data("movie_index.faiss"), dtype=np.uint8))
        new_movies = json.loads(read_data("movies.json"))
        # npy(pickle) 대신 csv: 네트워크에서 받은 pickle은 로드 시 코드 실행 위험
        new_reviews = pd.read_csv(io.BytesIO(read_data("movie_reviews.csv")), encoding="utf-8-sig").to_numpy()
    except Exception as e:
        print(f"⚠️ 데이터 로드 실패, 기존 데이터 유지: {e}")
        return

    # 인덱스 i번째 벡터 = movies[i] 이므로 개수가 다르면 깨진 데이터
    if new_index.ntotal != len(new_movies) or not new_movies:
        print(f"⚠️ 인덱스({new_index.ntotal})와 영화({len(new_movies)}) 개수 불일치, 기존 데이터 유지")
        return

    index, movies, movie_reviews = new_index, new_movies, new_reviews
    print(f"✅ 데이터 로드 성공: 영화 {len(movies)}개, 리뷰 {len(movie_reviews)}개")

load_data()

# 임베딩 함수
def query_embedding(text):    
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32).reshape(1, -1)

# 리뷰 샘플링 함수 (GPT 요약 제거, Raw Text 제공)
def get_movie_context(movie_title, max_reviews=3):
    # 해당 영화의 리뷰 필터링
    reviews = movie_reviews[movie_reviews[:, 0] == movie_title]
    review_texts = []
    
    if len(reviews) > 0:
        # 최신 순 혹은 랜덤으로 몇 개만 뽑음 (여기서는 랜덤)
        # 긍정/부정 골고루 뽑으면 좋음 (평점순 정렬 후 상/하위 추출 등)
        # 간단하게 랜덤 샘플링
        indices = np.random.choice(len(reviews), min(len(reviews), max_reviews), replace=False)
        for i in indices:
            row = reviews[i]
            # row[1]=작성자, row[2]=평점, row[3]=리뷰
            review_texts.append(f"- 평점 {row[2]}: {str(row[3])[:100]}") # 길이 제한

    return "\n".join(review_texts)

class QueryModel(BaseModel):
    query: str

class AIResponse(BaseModel):
    answer: str = Field(description="사용자 질문에 대한 친절하고 상세한 답변 (Markdown 형식)")
    recommendations: list[str] = Field(description="답변에서 추천하거나 언급한 영화들의 정확한 제목 리스트")

# 통합된 답변 생성 함수 (Single-Shot)
async def generate_ai_response_unified(query, candidate_movies, history):
    """
    통합 RAG (스트리밍 버전): 검색된 영화 정보와 이전 대화를 바탕으로 답변을 "스트리밍"으로 생성.
    마지막에 <<<REC>>> 구분자를 쓰고 추천 영화 목록(JSON)을 붙임.
    """
    context_text = ""
    for idx, movie in enumerate(candidate_movies):
        context_text += (
            f"{idx+1}. {movie['제목']} (장르: {movie.get('장르', 'N/A')}, 평점: {movie.get('관람객 평점', 'N/A')}, "
            f"상영 시간: {movie.get('상영 시간', 'N/A')}, 개봉일: {movie.get('개봉일', 'N/A')}, "
            f"관객수: {movie.get('관객수', 'N/A')}, 박스오피스: {movie.get('급상승 순위', 'N/A')})\n"
        )
        context_text += f"   출연진: {movie.get('출연진', 'N/A')[:150]}\n"
        context_text += f"   줄거리: {movie.get('줄거리', 'N/A')[:200]}...\n"
        if "reviews" in movie and movie["reviews"]:
             # 리뷰 3개를 연결해서 제공 (각 80자 제한)
             reviews_summary = " | ".join([r[:80].replace("\n", " ") for r in movie['reviews']])
             context_text += f"   [관람객 반응]: {reviews_summary}\n"
        context_text += "\n"

    # 사용자 입력은 system 프롬프트에 끼워 넣지 않고 user 메시지로 분리 (프롬프트 인젝션 완화)
    system_prompt = f"""
    너는 영화 추천 전문가 'Filmio'야. 사용자와 대화를 이어가며 답해.

    [후보 영화 목록]
    {context_text}

    [지시사항]
    1. 사용자의 질문에 대해 친절하고 전문적으로 답변해줘. (마크다운 사용 가능)
    2. 이전 대화의 맥락을 반영해. "그거", "다른 거", "더 밝은 거" 같은 표현은 앞선 대화를 기준으로 해석해.
    3. 후보 영화 목록을 참고하되, 질문과 관련 없는 영화는 언급하지 마. 목록에 없는 영화 정보는 지어내지 마.
    4. 답변 끝에 **반드시** 추천하거나 언급한 영화 제목들을 아래 형식으로 붙여줘.
       (이 부분은 사용자가 볼 수 없게 처리될 거야)

    [출력 포맷 예시]
    (여기에 사용자에 대한 답변 작성)
    <<<REC>>>
    ["영화 제목1", "영화 제목2"]
    """
    try:
        stream = client.responses.create(
            model="gpt-5-mini",
            input=[{"role": "system", "content": system_prompt}, *history, {"role": "user", "content": query}],
            reasoning={"effort": "minimal"},
            stream=True
        )
        for event in stream:
            if event.type == "response.output_text.delta":
                yield event.delta

    except Exception as e:
        print(f"OpenAI API Error: {e}")
        yield f"에러가 발생했습니다: {str(e)}"

# --- [API Endpoints] ---

class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]  # 클라이언트가 system 역할을 주입하지 못하도록 제한
    content: str

class ChatRequest(BaseModel):
    input: str = Field(max_length=1000)
    history: list[ChatMessage] = []  # 서버는 대화를 저장하지 않음 (Cloud Run 인스턴스는 언제든 바뀜)

# 컨텍스트 관리: 최근 3턴(질문+답변 6개)만, 메시지당 1500자까지만 LLM에 전달해 비용·지연 상한을 둔다
MAX_HISTORY_MESSAGES = 6
MAX_MESSAGE_CHARS = 1500

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    query = request.input
    history = [{"role": m.role, "content": m.content[:MAX_MESSAGE_CHARS]} for m in request.history[-MAX_HISTORY_MESSAGES:]]
    print(f"사용자 입력: {query} (이전 메시지 {len(history)}개)")

    # "그거 말고 밝은 거" 같은 이어지는 질문은 단독으로는 검색 맥락이 없으므로 직전 질문과 합쳐 검색
    prev_question = next((m["content"] for m in reversed(history) if m["role"] == "user"), "")
    prev_answer = next((m["content"] for m in reversed(history) if m["role"] == "assistant"), "")
    search_text = f"{prev_question}\n{query}" if prev_question else query

    # shortcut: 요청 처리 중 동기로 다운로드(시간당 1회, 1~2초), 트래픽이 늘면 백그라운드 갱신으로 전환
    if time.time() - last_loaded > RELOAD_SECONDS:
        load_data()

    # 1. 임베딩 생성
    try:
        query_vec = query_embedding(search_text)
    except Exception as e:
        resp = StreamingResponse(iter([f"임베딩 에러: {e}"]), media_type="text/plain")
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    # 2. FAISS 검색
    try:
        if index is None:
            raise Exception("FAISS 인덱스가 로드되지 않았습니다.")
            
        distances, indices = index.search(query_vec, k=5)
        
        candidates = []
        for i, idx in enumerate(indices[0]):
            if idx < len(movies):
                movie_data = movies[idx].copy()
                # 리뷰 데이터 연결
                related_reviews = movie_reviews[movie_reviews[:, 0] == movie_data["제목"]]
                if len(related_reviews) > 0:
                    movie_data["reviews"] = related_reviews[:, 3].tolist()[:3]
                candidates.append(movie_data)
        
        # 3. 키워드 검색 (보완): 질문 또는 직전 답변에 나온 제목 ("그 영화 줄거리는?" 대응)
        for movie in movies:
            # 단순 포함 여부 체크 (중복 제외)
            if movie["제목"] in query or movie["제목"] in prev_answer:
                # 이미 candidates에 있는지 확인 (제목 기준)
                if not any(c["제목"] == movie["제목"] for c in candidates):
                    movie_data = movie.copy()
                    related_reviews = movie_reviews[movie_reviews[:, 0] == movie_data["제목"]]
                    if len(related_reviews) > 0:
                        movie_data["reviews"] = related_reviews[:, 3].tolist()[:3]
                    candidates.append(movie_data)

    except Exception as e:
        resp = StreamingResponse(iter([f"검색 중 에러 발생: {e}"]), media_type="text/plain")
        resp.headers["Access-Control-Allow-Origin"] = "*"
        return resp

    # 4. 스트리밍 응답 반환
    resp = StreamingResponse(
        generate_ai_response_unified(query, candidates, history),
        media_type="text/plain"
    )
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


from fastapi.responses import FileResponse, StreamingResponse

# ... (기존 코드) ...

# --- [Frontend Serving] ---
# 루트 접속 시 index.html 반환
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(BASE_DIR, "..", "index.html"))

# 스타일시트 서빙
@app.get("/style.css")
async def serve_css():
    return FileResponse(os.path.join(BASE_DIR, "..", "style.css"))

# 이미지 파일 서빙 (src/img 폴더)
@app.get("/src/img/{filename}")
async def serve_images(filename: str):
    image_path = os.path.join(BASE_DIR, "..", "src", "img", filename)
    if os.path.exists(image_path):
        return FileResponse(image_path)
    return {"error": "Image not found"}

# 데이터 파일 서빙 (src/db 폴더 - movies.json, date.txt 등)
@app.get("/src/db/{filename}")
async def serve_db_files(filename: str):
    # 보안상 허용된 파일 확장자만 제공
    ALLOWED_EXTENSIONS = {".json", ".txt", ".csv"}
    _, ext = os.path.splitext(filename)
    
    if ext not in ALLOWED_EXTENSIONS:
        return {"error": "Access denied"}

    file_path = os.path.join(BASE_DIR, "db", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"error": "File not found"}

# 통계 API
@app.get("/stats")
async def get_stats():
    # ... (기존 통계 로직) ...
    """
    현재 DB에 저장된 영화 개수와 리뷰 개수를 반환합니다.
    """
    try:
        m_count = len(movies)
        r_count = len(movie_reviews)
        return {
            "movie_count": m_count,
            "review_count": r_count
        }
    except Exception as e:
        print(f"Stats Error: {e}")
        return {"movie_count": 0, "review_count": 0}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)