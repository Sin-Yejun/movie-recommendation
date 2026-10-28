# 🎬 Filmio - AI Movie Curator (Conversational RAG & Streaming)

**Filmio**는 현재 상영작 정보와 관객 리뷰를 매일 자동으로 수집·임베딩하고, 사용자와 대화하며 질문에 맞는 영화를 검색해 답변과 추천을 제공하는 AI 큐레이션 서비스입니다.
**RAG(벡터 검색 + 키워드 매칭)**, **대화 컨텍스트 관리**, **Streaming Response**를 적용했습니다.

🔗 https://movie.yejunsin.dev

![Filmio 화면: "반전 있는 스릴러 추천해줘"에 대한 답변과 추천 영화 카드](docs/screenshot-chat.png)

---

## 🔥 Key Features

### 1. 🧠 RAG (Retrieval-Augmented Generation)

- 벡터 검색(FAISS)과 키워드 매칭을 결합해 영화 후보군을 선별하고 프롬프트에 주입합니다.
- 임베딩 텍스트는 **제목 + 장르 + 줄거리 + 관객 리뷰 빈출 키워드**로 구성합니다. "여운이 남는", "웃긴" 같은 자연어 취향은 줄거리보다 관객 리뷰에 드러나기 때문입니다.
- **한 번의 LLM 호출**로 답변 생성과 추천 영화 목록 출력을 함께 처리합니다.

### 2. 💬 대화형 (컨텍스트 관리)

- 대화 기록은 브라우저가 보관하고 매 요청에 함께 보냅니다. 서버는 상태를 저장하지 않습니다 (Cloud Run 인스턴스는 언제든 교체될 수 있음).
- 서버는 **최근 3턴(6개 메시지), 메시지당 1,500자**만 LLM에 전달해 비용과 지연에 상한을 둡니다.
- "그거 말고 밝은 거" 같은 이어지는 질문은 **직전 질문과 합쳐서 검색**하고, **직전 답변에 나온 영화**도 후보에 포함합니다.
- 클라이언트가 보낸 메시지 역할은 `user`/`assistant`만 허용합니다 (`system` 역할 주입 차단).

### 3. 🔄 데이터 자동 갱신

- **GitHub Actions + Docker Compose**로 매일 KST 00시에 크롤링 → 임베딩 → 저장소 커밋을 실행합니다.
- **텍스트 해시(MD5) 기반 임베딩 캐시**: 텍스트가 바뀐 영화만 임베딩 API를 호출합니다.
- **실패 감지**: 수집 결과가 0건이거나 임베딩에 실패하면 데이터를 커밋하지 않고 Actions를 실패로 종료합니다.
- **서버는 재배포 없이 갱신**: 저장소의 최신 데이터를 1시간마다 다시 받아옵니다. FAISS 인덱스와 영화 수가 맞지 않으면 받은 데이터를 버리고 기존 데이터를 유지합니다.

### 4. ⚡ Real-Time Streaming

- **Server**: FastAPI의 `StreamingResponse`로 생성된 토큰을 실시간 전송합니다.
- **Client**: `ReadableStream`으로 받아 답변이 생성되는 즉시 마크다운으로 렌더링합니다.
- **Hybrid Response**: 텍스트 답변과 추천 영화 목록(JSON)을 `<<<REC>>>` 구분자로 하나의 스트림에 담아 보내고, 클라이언트가 영화 카드로 표시합니다.

---

## 🛠 Tech Stack

| Category     | Technology                                                                 |
| ------------ | -------------------------------------------------------------------------- |
| **Backend**  | Python 3.10, FastAPI, Uvicorn                                              |
| **AI / ML**  | OpenAI API (`gpt-6-luna`, `text-embedding-3-small`), FAISS                  |
| **Data**     | Selenium (Crawling), Pandas, NumPy                                         |
| **Frontend** | HTML5, CSS3, Vanilla JS (No Framework)                                     |
| **Infra**    | Google Cloud Run (API), GitHub Pages (Frontend), GitHub Actions + Docker Compose (Data Pipeline) |

---

## 🏗 Architecture

```
[GitHub Actions, 매일 KST 00시]
  Selenium 크롤링 (영화 정보, 리뷰) → 리뷰 키워드 추출 → 임베딩 (해시 캐시) → FAISS 인덱스
  → 저장소에 커밋 (src/db)
                         │  1시간마다 재로드
                         ▼
[브라우저 (GitHub Pages)] ── 질문 + 대화 기록 ──▶ [FastAPI (Cloud Run)] ── 검색 + 생성 ──▶ OpenAI
                         ◀────── 스트리밍 답변 + 추천 목록 ──────┘
```

---

## 📁 Project Structure

```bash
movie-recommendation/
├── src/
│   ├── db/
│   │   ├── movies.json             # 영화 메타데이터 (제목, 장르, 줄거리, 출연진, 평점 등)
│   │   ├── movie_reviews.csv       # 관객 리뷰 (실관람객, 네티즌, 평론가)
│   │   ├── movie_index.faiss       # FAISS 벡터 인덱스 (i번째 벡터 = movies.json의 i번째 영화)
│   │   ├── embedding_cache.pkl     # 텍스트 해시 → 임베딩 캐시
│   │   └── date.txt                # 마지막 갱신 날짜
│   ├── crawler_movie_info.py       # 영화 정보 크롤러 (Naver)
│   ├── crawler_movie_reviews.py    # 관객 리뷰 크롤러 (Naver)
│   ├── create_embedding.py         # 리뷰 키워드 추출, 임베딩 생성, FAISS 인덱스 빌드
│   └── server.py                   # FastAPI 백엔드 (대화형 Streaming RAG)
├── .github/workflows/crwal.yml     # 매일 데이터 갱신 (GitHub Actions)
├── docker-compose.yml              # Selenium + 크롤러 컨테이너
├── wait-for-it.sh                  # 파이프라인 실행: 크롤링 → 임베딩 → 커밋
├── Dockerfile                      # 크롤러 및 API 서버 이미지
├── deploy.ps1                      # Cloud Run 배포 스크립트
├── index.html                      # 프론트엔드 (영화 목록 + 채팅)
└── style.css
```

---

## 🚀 Getting Started

### 1. 환경 설정 (.env)

루트 디렉토리에 `.env` 파일을 만들고 OpenAI API 키를 설정하세요.

```ini
OPENAI_API_KEY=sk-proj-...
SELENIUM_URL=http://localhost:4444/wd/hub  # (크롤링 시 필요)
```

### 2. 데이터 준비 (크롤링 & 임베딩)

크롤러는 원격 Selenium에 접속합니다.

```bash
# 0. Selenium 실행
docker run -d -p 4444:4444 --shm-size=2g selenium/standalone-chrome

# 1. 영화 정보 수집
python src/crawler_movie_info.py

# 2. 리뷰 데이터 수집
python src/crawler_movie_reviews.py

# 3. 벡터 임베딩 생성 (FAISS 인덱스 빌드)
python src/create_embedding.py
```

### 3. 서버 실행

```bash
uvicorn src.server:app --reload --port 3000
```

- 서버는 기본적으로 **GitHub 저장소의 최신 데이터**를 받아오고, 실패하면 `src/db`의 로컬 파일을 사용합니다. 데이터 위치는 `DATA_URL` 환경변수로 바꿀 수 있습니다.
- `http://localhost:3000`에 접속하면 프론트엔드가 열립니다. 단, `index.html`은 배포된 API 주소를 호출하므로 로컬 API로 테스트하려면 `sendMessage`의 `url`을 바꿔야 합니다.

### 4. 배포

- **API**: `deploy.ps1` (Cloud Run, 서울 리전)
- **Frontend**: `master`에 push하면 GitHub Pages가 자동 배포합니다.

---

## 💡 How It Works (Internal Logic)

1. **User Input**: 사용자가 "스릴러 영화 추천해줘"라고 입력하면, 브라우저가 질문과 이전 대화 기록을 함께 보냅니다.
2. **Context Trimming**: 서버가 최근 3턴만 남깁니다.
3. **Embedding**: 질문(이어지는 질문이면 직전 질문 포함)을 벡터로 변환합니다 (`text-embedding-3-small`).
4. **Retrieval**: FAISS에서 가장 유사한 영화 5편을 찾고, 질문이나 직전 답변에 제목이 나온 영화를 추가합니다.
5. **Context Injection**: 후보 영화의 정보(장르, 평점, 상영 시간, 출연진, 줄거리)와 리뷰 3개를 문맥으로 조합합니다.
6. **Generation (Streaming)**:
   - GPT-6 Luna가 문맥과 대화 기록을 보고 답변을 생성합니다.
   - 서버는 첫 단어부터 클라이언트로 스트리밍 전송합니다.
   - 답변이 끝나면 `<<<REC>>>` 구분자와 함께 추천 영화 제목 리스트(JSON)를 보냅니다.
7. **Rendering**: 클라이언트는 답변을 대화 스레드에 마크다운으로 표시하고, JSON을 파싱해 **영화 카드**를 띄웁니다.
