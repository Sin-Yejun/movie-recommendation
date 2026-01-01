# 🎬 Filmio - AI Movie Curator (Single-Shot RAG & Streaming)

**Filmio**는 사용자의 질문을 이해하고, 실시간으로 영화 정보를 검색하여 맞춤형 답변과 추천을 제공하는 AI 큐레이션 서비스입니다.
**Single-Shot RAG** 기법과 **Streaming Response**를 적용하여, 빠르고 자연스러운 대화 경험을 제공합니다.

---

## 🔥 Key Features

### 1. 🧠 Single-Shot RAG (Retrieval-Augmented Generation)

- 기존의 복잡한 Multi-Turn 방식 대신, **단 한 번의 LLM 호출**로 '의도 파악 + 답변 생성 + 영화 추천'을 동시에 수행합니다.
- 벡터 검색(FAISS)과 키워드 매칭을 결합하여 최적의 영화 후보군(Candidates)을 선별하고 프롬프트에 주입합니다.

### 2. ⚡ Real-Time Streaming

- **Server**: FastAPI의 `StreamingResponse`를 통해 생성된 토큰을 실시간으로 전송합니다.
- **Client**: 브라우저에서 `ReadableStream`을 사용하여 답변이 생성되는 즉시 타이핑 효과와 함께 출력합니다.
- **Hybrid Response**: 텍스트 답변과 구조화된 데이터(JSON 추천 목록)를 하나의 스트림으로 받아 처리합니다.

### 3. 🎨 Modern UI/UX

- **Theme**: Dark & Glassmorphism (Deep Navy Gradient + Translucent Cards).
- **Layout**: 2-Column Dashboard (Movie Grid + Chat Panel).
- **Interactive**: 포스터 클릭 시 자동 질문 생성, 반응형 디자인 적용.

---

## 🛠 Tech Stack

| Category     | Technology                                                              |
| ------------ | ----------------------------------------------------------------------- |
| **Backend**  | Python 3.12, FastAPI, Uvicorn                                           |
| **AI / ML**  | OpenAI API (`gpt-4o-mini`), FAISS (Vector DB), `text-embedding-3-small` |
| **Data**     | Selenium (Crawling), NumPy, Pandas                                      |
| **Frontend** | HTML5, CSS3, Vanilla JS (No Framework)                                  |

---

## 📁 Project Structure

```bash
movie-recommendation/
├── src/
│   ├── db/
│   │   ├── movies.json            # 크롤링된 영화 메타 데이터
│   │   ├── movie_reviews.npy      # 리뷰 데이터 (NumPy)
│   │   └── movie_index.faiss      # FAISS 벡터 인덱스
│   ├── crawler_movie_info.py      # 영화 상세 정보 크롤러 (Naver)
│   ├── crawler_movie_reviews.py   # 실관람객 리뷰 크롤러
│   ├── create_embedding.py        # 벡터 임베딩 생성 및 FAISS 인덱싱
│   └── server.py                  # FastAPI 백엔드 서버 (Streaming RAG)
├── index.html                     # 메인 프론트엔드 (Dashboard UI)
├── style.css                      # 스타일시트 (Glassmorphism)
└── README.md
```

---

## 🚀 Getting Started

### 1. 환경 설정 (.env)

루트 디렉토리에 `.env` 파일을 생성하고 OpenAI API 키를 설정하세요.

```ini
OPENAI_API_KEY=sk-proj-...
SELENIUM_URL=http://localhost:4444/wd/hub  # (크롤링 시 필요)
```

### 2. 데이터 준비 (크롤링 & 임베딩)

```bash
# 1. 영화 정보 수집
python src/crawler_movie_info.py

# 2. 리뷰 데이터 수집
python src/crawler_movie_reviews.py

# 3. 벡터 임베딩 생성 (FAISS 인덱스 빌드)
python src/create_embedding.py
```

### 3. 서버 실행

```bash
# 포트 3000에서 서버 시작 (Hot Reload 모드)
uvicorn src.server:app --reload --port 3000
```

### 4. 접속

브라우저에서 `http://localhost:3000` (또는 `index.html` 직접 실행) 접속.

---

## 💡 How It Works (Internal Logic)

1. **User Input**: 사용자가 "스릴러 영화 추천해줘"라고 입력.
2. **Embedding**: 질문을 벡터로 변환 (`text-embedding-3-small`).
3. **Retrieval**: FAISS에서 가장 유사한 영화 5편 + 키워드 매칭 영화 검색.
4. **Context Injection**: 검색된 영화들의 줄거리와 **실관람객 리뷰**를 문맥으로 조합.
5. **Generation (Streaming)**:
   - GPT-5-mini가 문맥을 보고 답변을 생성하기 시작.
   - 서버는 첫 단어부터 클라이언트로 스트리밍 전송.
   - 답변 완료 후 `<<<REC>>>` 구분자와 함께 추천 영화 제목 리스트(JSON) 전송.
6. **Rendering**: 클라이언트는 텍스트를 마크다운으로 보여주고, 마지막에 도착한 JSON을 파싱해 **영화 카드**를 띄움.
