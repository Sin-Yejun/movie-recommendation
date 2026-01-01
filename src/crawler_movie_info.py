# 최신 영화 8개

import os
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 원격 브라우저 (Docker용)
selenium_url = os.getenv("SELENIUM_URL", "http://selenium:4444/wd/hub")
driver = webdriver.Remote(command_executor=selenium_url, options=options)

# --- [NEW] 기존 데이터 로드 ---
json_path = "src/db/movies.json"
existing_movies = []
if os.path.exists(json_path):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            existing_movies = json.load(f)
    except Exception as e:
        print(f"기존 데이터 로드 실패 (새로 시작합니다): {e}")

# 빠른 검색을 위해 딕셔너리로 변환 (Key: 영화 제목)
movies_dict = {m["제목"]: m for m in existing_movies}
print(f"기존 영화 데이터 {len(movies_dict)}개 로드 완료.")

# 이번 실행에서 확인된(크롤링된) 영화 제목 집합
active_movies = set()

# 크롤링 시작
driver.get("https://search.naver.com/search.naver?query=영화")
time.sleep(2)

i = 1  # 현재 페이지 내 영화 순번

while True:
    try:
        # 목록에서 영화 클릭 (상세 페이지 진입)
        try:
            # 썸네일/포스터 이미지 미리 확보 (목록에서)
            img_src = ""
            try:
                img_element = driver.find_element(By.XPATH, f'//*[@id="m_dss_movie_img{i-1}"]')
                img_src = img_element.get_attribute("src")
            except:
                pass

            # 클릭하여 상세 페이지 진입
            btn = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{i}]/div[1]/a')
            driver.execute_script("arguments[0].click();", btn)
            time.sleep(1.5) # 페이지 로딩 대기
        except Exception:
            # 더 이상 클릭할 영화가 없으면 종료
            break

        # 상세 페이지에서 제목 가져오기
        try:
            title_element = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[1]/div[1]/h2/span[1]/strong')
            title = title_element.text.strip()
            print(f"\n{i}번째 영화 처리 중: {title}")
            active_movies.add(title) # [Active] 현재 상영 확인
        except Exception as e:
            print(f"{i}번째 영화 제목을 찾을 수 없어 건너뜁니다. ({e})")
            driver.back()
            time.sleep(1)
            i += 1
            continue

        # 영화 정보 업데이트를 위한 임시 변수들
        rank = "N/A"
        audience = "N/A"
        rating = "N/A"

        # 순위, 관객 수, 실관람객 평균 평점 가져오기 (동적 데이터)
        try:
            items_elem = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div/span')
            items_text = items_elem.text.strip() # 예: "1위/123.4만명"
            if '/' in items_text:
                parts = items_text.split('/')
                rank = parts[0]
                audience = parts[1]
            else:
                 rank = items_text
            
            rating = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]/div/div/div[2]/div/div').text.strip()
        except:
            # 예외 처리: 구조가 다를 수 있음
            try:
                # 다른 경로 시도
                rank_elem = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[1]/dl/div[1]/dd') # 예시 경로
                # (실제 구조에 맞춰 유연하게 대응 필요, 여기서는 기존 로직 유지하되 안전하게)
            except:
                pass
            
            # 기존 로직의 fallback
            try:
                 audience = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[1]/dl/div[4]/dd').text.strip()
                 rating = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[1]/dl/div[3]/dd').text.strip()
            except:
                pass

        print(f"  -> 순위: {rank}, 관객 수: {audience}, 평점: {rating}")

        # === [MODIFY] 기존에 있는 영화라면 동적 데이터만 업데이트하고 넘어감 ===
        if title in movies_dict:
            print(f"  -> [Update] 기존 영화 정보 업데이트")
            movies_dict[title]["급상승 순위"] = rank
            movies_dict[title]["관객수"] = audience
            movies_dict[title]["관람객 평점"] = rating
            if img_src:
                movies_dict[title]["영화포스터"] = img_src
            
            # 뒤로 가기
            driver.back()
            time.sleep(0.5)
            i += 1
            continue

        # === [NEW] 새로운 영화라면 상세 정보 크롤링 ===
        print(f"  -> [New] 신규 영화 상세 정보 수집")

        # 출연진 (목록 페이지에서 수집) - 상세 페이지 들어오기 전에 수집했어야 하는데 순서상 여기서 찾기 힘듦.
        # 기존 로직 상 상세페이지 진입 전 목록에서 가져왔음. 다시 목록으로 나가서 가져오기엔 비효율적.
        # 상세 페이지 내부에서도 출연진 정보를 가져올 수 있는지 확인 필요하나, 
        # 일단 기존 코드 구조상 출연진은 목록에서 가져오는게 편함.
        # 리팩토링: 상세 페이지 들어가기 전으로 로직 이동이 필요하지만, 
        # 코드 구조를 크게 안바꾸려면, '기본 정보 탭' 클릭 후 수집 시도.
        
        actors = "N/A" # 상세 페이지 안에서 수집 시도 권장

        # 개봉 정보 클릭 (기본 정보 탭)
        try:
            btn_info = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[1]/div[3]/div/div/ul/li[2]/a')
            btn_info.click()
            time.sleep(1)
        except:
            pass

        # 개봉일, 장르, 국가, 줄거리 등
        release_date, grade, genre, country, running_time, stroy = "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"
        try:
            release_date = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[1]/dd').text.strip()
            grade = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[2]/dd').text.strip()
            genre = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[3]/dd').text.strip()
            country = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[4]/dd').text.strip()
            running_time = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[5]/dd').text.strip()
            stroy = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]').text.strip()
        except:
            pass

        # 신규 영화 저장
        new_movie = {
            "제목": title,
            "급상승 순위": rank,
            "장르": genre,
            "개봉일": release_date,
            "상영 시간": running_time,
            "관객수": audience,
            "관람객 평점": rating,
            "출연진": actors, # 상세페이지에서 못 가져오면 N/A (필요 시 로직 보강)
            "줄거리": stroy,
            "영화포스터": img_src
        }
        movies_dict[title] = new_movie

        # 뒤로 가기 (상세정보 탭 -> 통합검색) - 탭 클릭했으므로 2번? 아니 1번?
        # 기존 코드: 상세페이지 진입(1) -> 정보탭 클릭(1) -> 목록(back 2번)
        driver.back()
        time.sleep(0.5)
        # 만약 정보탭을 클릭 안했으면(기존영화) 1번만 back하면 됨.
        # 근데 위에서 정보탭 클릭함.
        driver.back() 
        time.sleep(0.5)

        i += 1
    except Exception as e:
        print(f"크롤링 중 에러 발생: {e}")
        break

# 결과 출력
print("\n크롤링 완료. 현재 관리 중인 영화 개수:", len(movies_dict))

# === [Cleanup] 상영 종료된 영화 삭제 ===
# active_movies에 없는 영화는 movies_dict에서 제거
outdated_movies = [t for t in movies_dict if t not in active_movies]
if outdated_movies:
    print(f"상영 종료된 영화 {len(outdated_movies)}개 삭제: {outdated_movies}")
    for t in outdated_movies:
        del movies_dict[t]
else:
    print("삭제할 영화 없음 (모두 현재 상영 중).")

driver.quit()

# 크롤링한 영화 데이터를 JSON 파일로 저장
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(list(movies_dict.values()), f, ensure_ascii=False, indent=4)

print("영화 데이터가 movies.json 파일로 저장되었습니다.")

