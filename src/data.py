import os
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import TextLoader
from collections import defaultdict
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 파일 로드
loader = TextLoader("reviews copy.txt")
docs = loader.load()

# 문서를 리뷰별로 파싱
reviews = docs[0].page_content.split('\n\n')
review_dict = defaultdict(list)
rating_dict = defaultdict(float)
idx = 0
for review in reviews:   
    lines = review.split('\n')
    try:
        title = lines[0].split(' : ')[1]
        rating = lines[1].split(' : ')[1]
        review = lines[2]
        rating_dict[title] += float(rating)
        review_dict[title].append(review)
    except:
        continue

for key in review_dict.keys():
     rating_dict[key] = round(rating_dict[key] / len(review_dict[key]),2)
     
# 임베딩 모델 생성
embeddings = OpenAIEmbeddings()

# 각 그룹(제목)에 대해 처리
for title, reviews in review_dict.items():
    
    combined_text = f"<{title}>".join(reviews)
    # 문서 분할
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, separators=["\n"], chunk_overlap=50)
    split_documents = text_splitter.split_text(combined_text)

    # 벡터 DB 생성 및 저장
    vectorstore = FAISS.from_texts(split_documents, embedding=embeddings)
    vectorstore.save_local(f'./db/faiss_{title}')

print("리뷰 데이터가 성공적으로 DB에 저장되었습니다.")
