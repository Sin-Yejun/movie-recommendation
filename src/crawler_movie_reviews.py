# 최신 영화 8개

import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
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


# 크롤링 시작
driver.get("https://search.naver.com/search.naver?query=영화")
time.sleep(2)

k = 1  # 현재 페이지 내 영화 순번
new_reviews = []  # 새로 수집된 리뷰

categories = [
    ('실관람객', '//ul/li/a/span[contains(text(), "실관람객")]', '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]'),
    ('네티즌', '//ul/li/a/span[contains(text(), "네티즌")]', '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]'),
    ('평론가', '//ul/li/a/span[contains(text(), "평론가")]', '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div')
]

while True:
    try:
        # 상세 페이지 클릭
        try:
            btn = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{k}]/div[1]/a')
            driver.execute_script("arguments[0].click();", btn)
        except:
            # 더 이상 클릭할 영화가 없으면 종료
            break
            
        time.sleep(1.5)

        # 상세 페이지에서 제목 가져오기 (Review ID 일관성 유지)
        try:
            title_element = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[1]/div[1]/h2/span[1]/strong')
            title = title_element.text.strip()
            print(f"\n{k}번째 영화 제목: {title}")
        except Exception as e:
            print(f"{k}번째 영화 제목 로드 실패 ({e}). 건너뜁니다.")
            driver.back() 
            time.sleep(1)
            k += 1
            continue

        # 관람평 메뉴 클릭
        try:
            driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[1]/div[3]/div/div/ul/li[5]/a').click()
            time.sleep(1)
        except:
            print(f"관람평 탭 못 찾음: {title}")
            driver.back() 
            time.sleep(0.5)
            k += 1
            continue

        idx = 4
        for category, tab_xpath, scroll_xpath in categories:
            print(category,'데이터 수집중...')
            # 탭 클릭
            try:
                driver.find_element(By.XPATH, tab_xpath).click()
                time.sleep(2)
            except:
                continue

            # 스포일러 토글 누르기
            if idx < 6:
                try:
                    button = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[{idx}]/div[2]/div[2]/button/span[1]')
                    driver.execute_script("arguments[0].click();", button)
                    time.sleep(1)
                except:
                    pass
                idx += 1

            # 스크롤 가능한 영역 찾기
            try:
                scrollable_div = driver.find_element(By.XPATH, scroll_xpath)
            except:
                continue
            
            # 스크롤 (너무 많이 하면 시간이 오래 걸리므로 적당히 제한을 두거나, 기존 로직 유지)
            # 여기서는 기존 로직 유지
            last_scroll_top = -1
            retry_scroll = 0
            while True:
                last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
                driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)
                time.sleep(0.5)
                new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
                if new_scroll_top == last_scroll_top:
                    retry_scroll += 1
                    if retry_scroll > 2: # 2번 더 시도해보고 진짜 끝이면 종료
                        break
                else:
                    retry_scroll = 0

            # 리뷰 크롤링
            i = 1
            
            # 페이지 내 모든 리뷰 요소 가져오기 (비효율적일 수 있으나 DOM 변화 감지 어려우므로 루프)
            # 기존 로직: `last` 변수로 중복 체크.
            # 개선: `existing_reviews_set` 으로 중복 체크.
            
            items_list = []
            scores_list = []
            
            # XPath 패턴 분석: ul/li[{i}]
            # 한 번에 elements 가져오는 게 빠를 수 있음.
            if category == '평론가':
                items = driver.find_elements(By.XPATH, f'{scroll_xpath}/ul/li/div[3]/span')
                # 평론가는 점수 위치가 다를 수 있음. 기존 코드 참고:
                # scores = driver.find_elements(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[1]/div/div[2]') <- 루프 안에서 i 사용
                # 평론가 점수는 보통 div[2]/div/div ... 
                # 기존 코드가 좀 불안정해 보이지만 일단 기존 XPATH 구조 유지하되 루프 방식 개선
            else:
                pass
            
            # 기존 루프 방식 유지하되 중복 체크 추가
            consecutive_dupes = 0 # 연속 중복 횟수 (너무 많으면 이미 수집한 구간이라 판단하고 break)
            
            while True:
                try:
                    # '더보기' 버튼 클릭 (긴 리뷰)
                    try:
                        btn_more = driver.find_element(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[2]/div/button')
                        driver.execute_script("arguments[0].click();", btn_more)
                    except:
                        pass
                    
                    review_text_elem = None
                    score_elem = None
                    
                    if category == '평론가':
                        review_text_elem = driver.find_element(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[3]/span')
                        score_elem = driver.find_element(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[1]/div/div[2]')
                    else:
                        review_text_elem = driver.find_element(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[2]/div/span')
                        score_elem = driver.find_element(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[1]/div/div[2]')
                    
                    review_text = review_text_elem.text.strip()
                    try:
                        score = float(score_elem.text.split('\n')[-1])
                    except:
                        score = 0.0
                    
                    # 중복 체크 키
                    # float 비교는 위험하므로 문자열 포맷팅
                    review_key = (title, category, score, review_text) # 값 비교
                     # 주의: score가 float라서 10.0 과 10 은 다를 수 있음.
                     # 하지만 들어갈때 float로 변환했음.
                    
                    # 튜플 비교 (Pandas to_records도 float는 float로 둠)
                    if review_key in existing_reviews_set:
                        consecutive_dupes += 1
                        if consecutive_dupes > 10: # 10개 연속 중복이면 더 이상 볼 필요 없음
                            print(f"  -> 이전에 수집된 리뷰 구간입니다. 다음 탭으로 이동.")
                            break
                    else:
                        new_reviews.append([title, category, score, review_text])
                        existing_reviews_set.add(review_key) # 이번 실행 내에서도 중복 방지
                        consecutive_dupes = 0
                    
                    i += 1
                except:
                    # 더 이상 li가 없으면
                    break

        k += 1
        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
        
    except Exception as e:
        print(f"{k} 페이지 오류 또는 크롤링 종료: {e}")
        break

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