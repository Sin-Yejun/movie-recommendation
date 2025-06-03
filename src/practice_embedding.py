import openai
import json
import numpy as np
import faiss
from sklearn.metrics.pairwise import cosine_similarity
import os
import time

# ✅ 환경 변수에서 API 키 읽기 (또는 직접 할당 가능)
openai.api_key = os.getenv("OPENAI_API_KEY")
# openai.api_key = "your-api-key"  # 직접 입력도 가능

# ✅ 경로 설정
MOVIE_PATH = 'src/db/movies.json'
EMBEDDING_PATH = 'src/cache/embeddings.npy'
INDEX_PATH = 'src/cache/faiss.index'

# ✅ 1. 영화 데이터 로드
with open(MOVIE_PATH, 'r', encoding='utf-8') as f:
    movies = json.load(f)

# ✅ 2. 검색용 텍스트 구성
movie_texts = [
    f"{movie['제목']}. 장르: {movie['장르']}. 출연: {movie['출연진']}. 줄거리: {movie['줄거리']}"
    for movie in movies
]

# ✅ 3. OpenAI 임베딩 함수
def get_embedding(text, model="text-embedding-3-small"):
    try:
        response = openai.embeddings.create(
            input=[text],
            model=model
        )
        return np.array(response.data[0].embedding, dtype=np.float32)
    except Exception as e:
        print(f"[❌] Embedding error: {e}")
        return None

# ✅ 4. 임베딩 전체 생성
def build_movie_embeddings(texts):
    embeddings = []
    for idx, text in enumerate(texts):
        print(f"[🔍] Embedding {idx+1}/{len(texts)}: {movies[idx]['제목']}")
        emb = get_embedding(text)
        if emb is not None:
            embeddings.append(emb)
        else:
            embeddings.append(np.zeros(1536, dtype=np.float32))  # 실패 시 0으로 채움
        time.sleep(0.5)  # API 호출 속도 제한 대응
    return embeddings

# ✅ 5. 저장 함수
def save_embeddings(embeddings, index):
    os.makedirs(os.path.dirname(EMBEDDING_PATH), exist_ok=True)
    np.save(EMBEDDING_PATH, np.array(embeddings))
    faiss.write_index(index, INDEX_PATH)
    print("[✅] 임베딩 및 인덱스 저장 완료")

# ✅ 6. 로드 함수
def load_embeddings():
    if os.path.exists(EMBEDDING_PATH) and os.path.exists(INDEX_PATH):
        print("[📂] 저장된 임베딩과 인덱스를 불러옵니다.")
        loaded_embeddings = np.load(EMBEDDING_PATH)
        loaded_index = faiss.read_index(INDEX_PATH)
        return loaded_embeddings, loaded_index
    return None, None

# ✅ 7. 메인 흐름: 로드 또는 새로 생성
embeddings, index = load_embeddings()

if embeddings is None:
    print("[🚀] 임베딩 생성 중...")
    embeddings = build_movie_embeddings(movie_texts)
    
    embedding_dim = len(embeddings[0])
    index = faiss.IndexFlatL2(embedding_dim)
    index.add(np.array(embeddings))

    save_embeddings(embeddings, index)

# ✅ 8. 검색 함수 (Re-ranking 포함)
def search_with_reranking(query, top_k=3):
    query_embedding = get_embedding(query).reshape(1, -1)
    distances, indices = index.search(query_embedding, top_k)
    candidate_indices = indices[0]

    candidate_embeddings = np.array([embeddings[i] for i in candidate_indices])
    sim_scores = cosine_similarity(query_embedding, candidate_embeddings)[0]
    reranked_indices = candidate_indices[np.argsort(-sim_scores)]

    return [movies[i] for i in reranked_indices]

# ✅ 9. 실행부
if __name__ == "__main__":
    query = input("🎯 검색어를 입력하세요: ")
    results = search_with_reranking(query, top_k=3)

    print("\n🎬 검색 결과:")
    for i, movie in enumerate(results, 1):
        print(f"\n{i}. [{movie['제목']}]")
        print(f"장르: {movie['장르']}")
        print(f"관람객 평점: {movie['관람객 평점']}")
        print(f"출연진: {movie['출연진']}")
        print(f"줄거리: {movie['줄거리']}...")
