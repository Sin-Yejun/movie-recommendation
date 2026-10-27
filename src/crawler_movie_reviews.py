# 최신 영화 8개

import os
import sys
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.chrome.options import Options
import json

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 원격 브라우저 (Docker용)
selenium_url = os.getenv("SELENIUM_URL", "http://selenium:4444/wd/hub")
driver = webdriver.Remote(command_executor=selenium_url, options=options)

# --- [SYNC] Step 1. 유효한 영화 목록 로드 (movies.json 기준) ---
json_path = "src/db/movies.json"
valid_titles = set()
if os.path.exists(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            movies_data = json.load(f)
            valid_titles = {m["제목"] for m in movies_data}
        print(f"현재 유효한 상영작 {len(valid_titles)}개 로드: {valid_titles}")
    except Exception as e:
        print(f"영화 목록 로드 실패: {e}")

# --- [NEW] 기존 리뷰 데이터 로드 및 정제 ---
csv_path = 'src/db/movie_reviews.csv'
if os.path.exists(csv_path):
    try:
        existing_df = pd.read_csv(csv_path, encoding='utf-8-sig')
        
        # [CLEANUP] 유효하지 않은 영화(상영 종료)의 리뷰 삭제
        original_count = len(existing_df)
        existing_df = existing_df[existing_df['제목'].isin(valid_titles)]
        cleaned_count = len(existing_df)
        
        if original_count > cleaned_count:
            print(f"오래된 영화의 리뷰 {original_count - cleaned_count}건 삭제됨.")

        # 중복 체크를 위한 Set 생성
        existing_reviews_set = set(
            tuple(x) for x in existing_df[['제목', '작성자유형', '평점', '리뷰']].to_records(index=False)
        )
        print(f"기존 리뷰 {len(existing_reviews_set)}개 유지 중 (유효 영화 기준).")
    except Exception as e:
        print(f"기존 리뷰 파일 로드 실패: {e}")
        existing_reviews_set = set()
        existing_df = pd.DataFrame(columns=['제목', '작성자유형', '평점', '리뷰'])
else:
    existing_reviews_set = set()
    existing_df = pd.DataFrame(columns=['제목', '작성자유형', '평점', '리뷰'])


# 크롤링 시작: 목록에서 제목·링크를 먼저 모은 뒤 각 페이지로 직접 이동 (클릭/뒤로가기 X)
# 네이버는 클래스명에 빌드 해시가 붙으므로(_commentBody_1d1t6_115 등) 접두어/라벨 텍스트 기준으로 찾는다
driver.get("https://search.naver.com/search.naver?query=영화")
time.sleep(2)

cards = []
for img in driver.find_elements(By.CSS_SELECTOR, '[id^="m_dss_movie_img"]'):
    link = img.find_elements(By.XPATH, './ancestor::a[1]')
    title = (img.get_attribute("alt") or "").strip()
    if link and title in valid_titles:
        cards.append((title, link[0].get_attribute("href")))
print(f"리뷰 수집 대상 영화 {len(cards)}개")
if not cards:
    driver.quit()
    sys.exit("리뷰를 수집할 영화를 찾지 못했습니다 (네이버 페이지 구조 변경 의심).")

new_reviews = []  # 새로 수집된 리뷰
MAX_PAGES = 20    # 탭당 최대 페이지 수 (페이지당 5개)

for k, (title, href) in enumerate(cards, 1):
    try:
        print(f"\n{k}번째 영화 제목: {title}")
        driver.get(href)
        time.sleep(1.5)

        # 평점 페이지 (상세 카드의 '평점 남기기' 링크 = "{제목} 평점" 검색)
        link = driver.find_elements(By.XPATH, '//a[normalize-space()="평점 남기기"]')
        driver.get(link[0].get_attribute("href") if link else f"https://search.naver.com/search.naver?query={title} 평점")
        time.sleep(1.5)

        for category in ['실관람객', '네티즌', '평론가']:
            print(category, '데이터 수집중...')
            try:
                tab = driver.find_element(By.XPATH, f'//li[@role="tab"]//span[normalize-space()="{category}"]')
                driver.execute_script("arguments[0].click();", tab)
                time.sleep(1.5)
            except Exception:
                print(f"  -> {category} 탭 없음")
                continue

            # 최신순 정렬: 새 리뷰가 앞에 오므로, 전부 중복인 페이지가 나오면 멈춘다
            for sort_btn in driver.find_elements(By.XPATH, '//button[normalize-space()="최신순"]'):
                driver.execute_script("arguments[0].click();", sort_btn)
                time.sleep(1)

            for page in range(MAX_PAGES):
                page_new = 0
                for body in driver.find_elements(By.XPATH, '//p[contains(@class, "_commentBody_")]'):
                    review_text = body.get_attribute("textContent").strip()
                    try:
                        item = body.find_element(By.XPATH, './ancestor::div[.//strong[contains(@class, "_score_")]][1]')
                        score = float(item.find_element(By.XPATH, './/strong[contains(@class, "_score_")]').get_attribute("textContent"))
                    except Exception:
                        score = 0.0

                    review_key = (title, category, score, review_text)
                    if review_text and review_key not in existing_reviews_set:
                        new_reviews.append([title, category, score, review_text])
                        existing_reviews_set.add(review_key)  # 이번 실행 내에서도 중복 방지
                        page_new += 1

                if page_new == 0:
                    break  # 이전에 수집된 구간
                next_btn = driver.find_elements(By.CSS_SELECTOR, 'button.cmm_pg_next')
                if not next_btn or not next_btn[0].is_enabled():
                    break  # 마지막 페이지
                driver.execute_script("arguments[0].click();", next_btn[0])
                time.sleep(1)
    except Exception as e:
        print(f"  -> {title} 리뷰 수집 중 에러 발생, 건너뜁니다: {e}")

print(f"\n크롤링 완료. 새로 추가된 리뷰 개수: {len(new_reviews)}")
driver.quit()

# 데이터 프레임 생성 및 병합
if new_reviews:
    new_df = pd.DataFrame(new_reviews, columns=['제목', '작성자유형', '평점', '리뷰'])
    final_df = pd.concat([existing_df, new_df], ignore_index=True)
    # CSV 파일로 저장
    final_df.to_csv('src/db/movie_reviews.csv', index=False, encoding='utf-8-sig')
    print("CSV 파일 업데이트 완료: movie_reviews.csv")
else:
    print("새로운 리뷰가 없어 파일을 업데이트하지 않았습니다.")