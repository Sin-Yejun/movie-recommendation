# 최신 영화 8개

import os
import sys
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
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

# 네이버는 클래스명에 빌드 해시가 붙으므로(_cmTopTitle_1hp0o_19 등) 화면 라벨 텍스트 기준으로 찾는다
def text_of(xpath):
    try:
        return driver.find_element(By.XPATH, xpath).get_attribute("textContent").strip()
    except Exception:
        return "N/A"

def dd(label):      # <dt>개봉</dt><dd>2026.10.21.</dd>
    return text_of(f'//dt[normalize-space()="{label}"]/following-sibling::dd[1]')

def metric(label):  # <span>순위</span><span>3위</span>
    return text_of(f'//span[normalize-space()="{label}"]/following-sibling::span[1]')

# 크롤링 시작: 목록에서 제목·링크·포스터를 먼저 모은 뒤 각 페이지로 직접 이동 (클릭/뒤로가기 X)
driver.get("https://search.naver.com/search.naver?query=영화")
time.sleep(2)

cards = []
for img in driver.find_elements(By.CSS_SELECTOR, '[id^="m_dss_movie_img"]'):
    link = img.find_elements(By.XPATH, './ancestor::a[1]')
    title = (img.get_attribute("alt") or "").strip()
    if link and title:
        cards.append((title, link[0].get_attribute("href"), img.get_attribute("src") or ""))
print(f"목록에서 영화 {len(cards)}개 발견")

for i, (title, href, img_src) in enumerate(cards, 1):
    try:
        print(f"\n{i}번째 영화 처리 중: {title}")
        driver.get(href)
        time.sleep(1.5)

        # 순위, 관객 수, 실관람객 평점 (동적 데이터)
        rank = metric("순위")
        audience = metric("누적관객수")
        rating = metric("실관람객")
        print(f"  -> 순위: {rank}, 관객 수: {audience}, 평점: {rating}")
        active_movies.add(title)  # [Active] 현재 상영 확인

        # === 기존에 있는 영화라면 동적 데이터만 업데이트하고 넘어감 ===
        if title in movies_dict:
            print(f"  -> [Update] 기존 영화 정보 업데이트")
            movies_dict[title]["급상승 순위"] = rank
            movies_dict[title]["관객수"] = audience
            movies_dict[title]["관람객 평점"] = rating
            if img_src:
                movies_dict[title]["영화포스터"] = img_src
            continue

        # === 새로운 영화라면 상세 정보 크롤링 ===
        print(f"  -> [New] 신규 영화 상세 정보 수집")

        # 감독/출연 (메인 카드): "연상호 감독", "김현주 류소영 역" ...
        members = driver.find_elements(By.XPATH, '//strong[normalize-space()="감독/출연"]/following-sibling::div//li')
        actors = ", ".join(
            " ".join(" ".join(e.get_attribute("textContent") for e in li.find_elements(By.XPATH, './/*[not(*)]')).split())
            for li in members
        ) or "N/A"

        # 상세 정보 페이지 (줄거리 '더보기' 링크 = "{제목} 정보" 검색)
        more = driver.find_elements(By.XPATH, '//a[contains(@class, "_moreLink")]')
        driver.get(more[0].get_attribute("href") if more else f"https://search.naver.com/search.naver?query={title} 정보")
        time.sleep(1.5)

        release_date, genre, running_time = dd("개봉"), dd("장르"), dd("러닝타임")

        # 줄거리는 '펼쳐보기'를 눌러야 전체가 DOM에 들어옴
        try:
            driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, '//button[normalize-space()="펼쳐보기"]'))
            time.sleep(0.5)
        except Exception:
            pass
        stroy = text_of('//span[contains(@class, "_desc_")]').replace("펼쳐보기", "").replace("접기", "").strip()

        # 신규 영화 저장
        movies_dict[title] = {
            "제목": title,
            "급상승 순위": rank,
            "장르": genre,
            "개봉일": release_date,
            "상영 시간": running_time,
            "관객수": audience,
            "관람객 평점": rating,
            "출연진": actors,
            "줄거리": stroy,
            "영화포스터": img_src
        }
    except Exception as e:
        print(f"  -> {title} 처리 중 에러 발생, 건너뜁니다: {e}")

# 결과 출력
print("\n크롤링 완료. 현재 관리 중인 영화 개수:", len(movies_dict))

# 하나도 못 가져왔다면 페이지 구조가 바뀐 것: 기존 데이터를 지우지 않고 실패로 종료
if not active_movies:
    driver.quit()
    sys.exit("영화를 하나도 수집하지 못했습니다 (네이버 페이지 구조 변경 의심). 기존 데이터를 유지합니다.")

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

