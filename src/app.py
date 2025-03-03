import asyncio
from typing import AsyncIterable, List
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain.callbacks import AsyncIteratorCallbackHandler
from pydantic import BaseModel
from langchain_community.chat_models import ChatOllama
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.runnables import RunnablePassthrough
from langchain_community.llms import Ollama
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os


# langchain의 기록을 확인할 수 있습니다.
import langchain
langchain.debug = True

# 환경변수를 만듭니다.
load_dotenv()

# 임베딩 생성
embeddings = OpenAIEmbeddings()

vectorstore_paths = [d for d in os.listdir('./db') if os.path.isdir(os.path.join('./db', d))]
retrievers = []

for path in vectorstore_paths:
    vectorstore = FAISS.load_local('./db/'+path, embeddings=embeddings, allow_dangerous_deserialization=True)
    retrievers.append(vectorstore.as_retriever())

# 문서 분할기 설정
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

# 여러 검색기에서 결과를 결합하는 함수
def combined_retriever(question: str) -> List[str]:
    combined_results = []
    for retriever in retrievers:
        results = retriever.get_relevant_documents(question)
        combined_results.extend(results)
    return combined_results

# 문서를 분할하여 처리하는 함수
def split_documents(documents: List[str]) -> List[str]:
    split_texts = []
    for doc in documents:
        split_texts.extend(text_splitter.split_text(doc.page_content))
    return split_texts

# API 서버 관련 셋팅
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    content: str


async def send_message(content: str) -> AsyncIterable[str]:

    # 모델을 불러옵니다.
    callback = AsyncIteratorCallbackHandler()
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0, streaming=True, callbacks=[callback])

    # LangChain이 지원하는 다른 채팅 모델을 사용합니다. 여기서는 Ollama를 사용합니다.
    prompt = ChatPromptTemplate.from_template("""
    You are an expert in recommending movies.
    Please base your answers solely on the data I provide.
    Do not answer anything beyond the given information.
    영화: 탈주, 순위: 2위, 누적 관객수 148만명, 관람객 평점: 8.75, 장르: 액션, 개봉일: 2024년 07월 03일, 배급사: 플러스엠 엔터테인먼트, 감독 : 이종필, 주연 배우: 이제훈, 구교환, 홍사빈, 줄거리: “내 앞 길 내가 정했습니다” 휴전선 인근 북한 최전방 군부대. 10년 만기 제대를 앞둔 중사 ‘규남’(이제훈)은 미래를 선택할 수 없는 북을 벗어나 원하는 것을 해 볼 수 있는 철책 너머로의 탈주를 준비한다. 그러나, ‘규남’의 계획을 알아챈 하급 병사 ‘동혁’(홍사빈)이 먼저 탈주를 시도하고, 말리려던 ‘규남’까지 졸지에 탈주병으로 체포된다. “허튼 생각 말고 받아들여. 이것이 니 운명이야” 탈주병 조사를 위해 부대로 온 보위부 소좌 ‘현상’(구교환)은 어린 시절 알고 지내던 ‘규남’을 탈주병을 체포한 노력 영웅으로 둔갑시키고 사단장 직속보좌 자리까지 마련해주며 실적을 올리려 한다. 하지만 ‘규남’이 본격적인 탈출을 감행하자 ‘현상’은 물러설 길 없는 추격을 시작한다.
    영화: 탈출, 순위: 4위, 누적 관객수 45만명, 관람객 평점: 5.57, 장르: 스릴러, 개봉일: 2024년 07월 12일, 배급사: CJ ENM, 감독 : 김태곤, 주연 배우: 이선균, 주지훈, 김희원, 줄거리: 붕괴 위기의 공항대교, 생존자 전원이 타겟이 되었다. 기상 악화로 한치 앞도 구분할 수 없는 공항대교. 연쇄 추돌 사고와 폭발로 붕괴 위기에 놓인 다리 위에 사람들이 고립된다. 이 때 극비리에 이송 중이던 '프로젝트 사일런스'의 군사용 실험견들이 풀려나고 모든 생존자가 그들의 타겟이 되어 무차별 공격당하는 통제불능의 상황이 벌어진다. 공항으로 향하던 안보실 행정관(이선균)부터 사고를 수습하려고 현장을 찾은 렉카 기사(주지훈), 그리고 실험견들을 극비리에 이송 중이던 '프로젝트 사일런스'의 책임연구원(김희원)까지. 사상 최악의 연쇄 재난 발생, 살아남기 위한 극한의 사투가 시작된다!
    영화: 인사이드 아웃 2, 순위: 3위, 누적 관객수 774만명, 관람객 평점: 9.44, 장르: 애니메이션, 개봉일: 2024년 06월 12일, 배급사: 월트디즈니 컴퍼니 코리아, 감독 : 켈시 맨, 주연 배우: 에이미 포엘러, 마야 호크, 루이스 블랙, 필리스 스미스, 토니 헤일, 줄거리: 디즈니·픽사의 대표작 <인사이드 아웃> 새로운 감정과 함께 돌아오다! 13살이 된 라일리의 행복을 위해 매일 바쁘게 머릿속 감정 컨트롤 본부를 운영하는 ‘기쁨’, ‘슬픔’, ‘버럭’, ‘까칠’, ‘소심’. 그러던 어느 날, 낯선 감정인 ‘불안’, ‘당황’, ‘따분’, ‘부럽’이가 본부에 등장하고, 언제나 최악의 상황을 대비하며 제멋대로인 ‘불안’이와 기존 감정들은 계속 충돌한다. 결국 새로운 감정들에 의해 본부에서 쫓겨나게 된 기존 감정들은 다시 본부로 돌아가기 위해 위험천만한 모험을 시작하는데… 2024년, 전 세계를 공감으로 물들인 유쾌한 상상이 다시 시작된다!
    영화: 핸섬가이즈, 순위: 5위, 누적 관객수 139만명, 관람객 평점: 9.29, 장르: 코미디, 개봉일: 2024년 06월 26일, 배급사: (주)NEW, 감독 : 남동협, 주연 배우: 이성민, 이희준, 공승연, 박지환, 이규형, 우현, 줄거리: “우리가 뭐 빠지는 게 있노? 집도 있고 차도 있고 인물도 훤칠한데” 자칭 터프가이 ‘재필’(이성민)과 섹시가이 ‘상구’(이희준) 현실은 잊지 못할 첫인상으로 이사 첫날부터 동네 경찰 ‘최 소장’(박지환)과 ‘남 순경’(이규형)의 특별 감시 대상이 되지만, 꿈꾸던 유럽풍 드림하우스에서 새출발 한다는 것에 그저 행복하기만 하다. 그러나 행복도 잠시, 물에 빠질 뻔한 ‘미나’(공승연)를 구해주려다 오히려 납치범으로 오해받는 상황이 이어진다. 한편 ‘미나’를 찾으러 온 불청객들을 시작으로 지하실에 봉인되어 있던 악령이 깨어나며 어두운 기운이 집안을 둘러싸기 시작하는데… “왜 다들 우리 집에 와서 죽고 난리야!”
    영화: 하이재킹, 순위: 6위, 누적 관객수 168만명, 관람객 평균 평점: 9.47, 장르: 범죄, 액션, 개봉일: 2024년 06월 21일, 배급사: 소니픽쳐스엔터테인먼트코리아㈜, ㈜키다리스튜디오, 감독 : 김성한, 주연 배우: 하정우, 여진구, 성동일, 채수빈, 줄거리: 1971년 겨울 속초공항 여객기 조종사 태인(하정우)과 규식(성동일)은 김포행 비행에 나선다. 승무원 옥순(채수빈)의 안내에 따라 탑승 중인 승객들의 분주함도 잠시, 이륙한지 얼마 되지 않아 사제폭탄이 터지며 기내는 아수라장이 된다. "지금부터 이 비행기 이북 간다" 여객기를 통째로 납치하려는 용대(여진구)는 조종실을 장악하고 무작정 북으로 기수를 돌리라 협박한다. 폭발 충격으로 규식은 한 쪽 시력을 잃고 혼란스러운 기내에서 절체절명의 상황에 처한 태인. 이들은 여객기를 무사히 착륙시키기 위한 사투를 시작하는데... 대한민국 상공 여객기 납치 사건 이 비행에 모두가 목숨을 걸었다!
    영화: 이매큘레이트, 순위: 7위, 누적 관객수 3905명, 관람객 평균 평점: 7.19, 장르: 공포, 개봉일: 2024년 07월 17일, 배급사: (주)디스테이션, 감독 : 마이클 모한, 주연 배우: 시드니 스위니, 알바로 모르테, 줄거리: 순수하고 신실한 믿음을 가진 수녀 '세실리아'(시드니 스위니). 어느 비밀스러운 수녀원의 초청을 받아 낯선 생활에 적응해 가던 중 처녀의 몸으로 임신을 했다는 사실이 밝혀지고 기적의 주인공으로 추앙 받기 시작하는데… 순결한 수녀의 임신, 축복인가 저주인가! 올여름, 충격적인 공포의 실체가 드러난다!
    영화: 코난, 순위: 1위, 누적 관객수 11만명, 관람객 평균 평점: 8.88, 장르: 애니메이션, 개봉일: 2024년 07월 17일, 배급사: CJ ENM, 감독 : 니가오카 치카, 주연 배우: 코난, 줄거리: 홋카이도 하코다테에 있는 ‘오노에’ 재벌 가의 창고에 ‘괴도 키드’의 예고장이 도착한다. ‘빅 주얼’만을 노리는 키드가 이번에 노리는 것은 과거 신선조 귀신 부장 ‘히지카타 토시조’와 얽힌 전설적인 검. 검술 대회에 참가하기 위해 하코다테에 방문한 ‘핫토리 헤이지’와 그를 응원하기 위해 온 ‘코난’ 일행도 괴도 키드를 막기 위해 사건에 뛰어들게 된다. 한편, 가슴에 열 십 자(十) 모양의 자상을 입은 시신이 발견되고 ‘죽음의 상인’이라고 불리는 무기상이 용의자로 지목된다. 그 역시 괴도 키드가 찾는 검을 노리고 있었고, 그 검이 오노에 가문이 세대에 걸쳐 지킨 보물을 찾을 열쇠임이 밝혀진다. 검을 쫓는 키드에게 수수께끼의 검사가 습격해 오고, 절체절명의 위기가 닥쳐오는데…! 검에 숨겨진 ‘진실’이 어두운 밤을 베고 달빛 아래 드러난다!
    영화: 플라이 미 투 더 문, 순위: 10위, 누적 관객수 3만명, 관람객 평균 평점: 8.19, 장르: 멜로/로맨스, 코미디, 개봉일: 2024년 07월 12일, 배급사: 소니픽쳐스, 감독 : 그렉 버랜티, 주연 배우: 스칼릿 조핸슨, 채닝 테이텀, 우디 해럴슨, 줄거리: 1960년대 우주 경쟁 시대, 거듭된 실패로 멀어진 대중들의 관심을 다시 모으기 위해 NASA는 아폴로 11호 발사를 앞두고 마케팅 전문가를 고용한다. 수단과 방법을 가리지 않고 NASA의 달 착륙을 홍보하는 마케터 켈리 존스와 그녀가 하는 일이 거짓말이라며 대립하는 발사 책임자 콜 데이비스. 전혀 다른 두 사람이 만났지만 하나의 목표를 위해 서서히 한마음이 되어간다. 미션의 성공이 눈앞에 보이기 시작한 가운데, 켈리 존스는 미 행정부에서 은밀한 제안을 받게 되고 실패도, 2등도 용납이 되지 않는 달 착륙 프로젝트를 위해 켈리 존스는 아무도 모르게 플랜 B, 즉 실패에 대비해 달 착륙 영상을 준비하기 시작하는데… 인류 최대의 업적, 최초의 달 착륙은 진짜일까, 가짜일까?
    The movies currently showing are ["탈주", "탈출", "인사이드 아웃 2", "핸섬가이즈", "하이재킹", "이매큘레이트", "코난", "플라이 미 투 더 문"].
    리뷰에 관한 내용을 물어보면 리뷰 그대로를 가져와서 읽어줘. 답변 문장을 너무 짧게 하지 말고 2줄 이상으로 해줘. 
    Answer in Korean. 무조건 말을 존댓말로 해.

    #Question: 
    {question} 

    #Answer:""")

    # 질문에 대한 검색 결과를 가져옵니다.
    retrieved_docs = combined_retriever(content)
    split_docs = split_documents(retrieved_docs)

    # 체인 생성
    chain = (
        {"context": lambda _: "\n".join(split_docs), "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    task = asyncio.create_task(
        chain.ainvoke(content)
    )

    # API에서 스트림 형식으로 출력되게끔 설정합니다.
    try:
        async for token in callback.aiter():
            yield token
    except Exception as e:
        print(f"Caught exception: {e}")
    finally:
        yield "\n"  # 답변이 끝난 후 줄바꿈 문자를 추가합니다.
        callback.done.set()

    await task


# API 서버 생성
@app.post("/stream_chat/") # 경로의 이름은 stream_chat입니다. request_test.py 파일에서 stream_chat을 붙여서 request 해야합니다.
async def stream_chat(message: Message):
    generator = send_message(message.content)
    return StreamingResponse(generator, media_type="text/event-stream")


# api서버 띄우기 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
