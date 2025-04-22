# 최신 영화 8개

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.chrome.options import Options
import json

options = Options()
options.add_argument("--headless")  # GUI 없이 실행
options.add_argument("--disable-gpu")  # GPU 가속 비활성화 (일부 환경에서 필요)
options.add_argument("--window-size=1920x1080")  # 화면 크기 설정

# WebDriver 실행
driver = webdriver.Chrome()
driver.get('https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%EC%98%81%ED%99%94')
time.sleep(2)

i = 1  # 현재 페이지 내 영화 순번
movie_list = []  # 영화 정보를 저장할 리스트

while True:
    try:
        # 영화 제목 가져오기
        title = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{i}]/div[1]/div/div[1]/div/a').text.strip()
        print(f"\n{i}번째 영화 제목: {title}")

        # 영화 포스터 이미지 가져오기
        img_element = driver.find_element(By.XPATH, f'//*[@id="m_dss_movie_img{i-1}"]')
        img_src = img_element.get_attribute("src")
        print(f"영화src: {img_src}")

        try:
            # 출연진 가져오기
            actors = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{i}]/div[1]/div/div[2]/dl[3]/dd/span').text.strip()
            print(f"출연진: {actors}")
        except:
            actors = "N/A"
        
        btn = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{i}]/div[1]/a')
        driver.execute_script("arguments[0].click();", btn)  # JavaScript로 클릭 실행
        time.sleep(1)


        # 순위, 관객 수, 실관람객 평균 평점 가져오기
        try:
            if title == '야당':
                items = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[5]/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div/span').text.strip()

            else:
                items = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div/span').text.strip()
            items = items.split('/')
            rank = items[0]
            audience = items[1]
            if title == '야당':
                rating = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[5]/div[2]/div[2]/div/div[2]/div/div/div[2]/div/div').text.strip()
            else:
                rating = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]/div/div/div[2]/div/div').text.strip()
        except:
            rank = "N/A"
            audience = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[1]/dl/div[4]/dd').text.strip()
            rating = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[1]/dl/div[3]/dd').text.strip()


        print(f"급상승 순위: {rank}\n관객 수: {audience}\n평균평점: {rating}")

        # 개봉 정보 클릭
        
        if title == '야당':
            btn = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[5]/div[1]/div[3]/div/div/ul/li[2]/a')
            btn.click()
        else:
            btn = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[1]/div[3]/div/div/ul/li[2]/a')
            btn.click()
        time.sleep(1)

        # 개봉일, 연령 제한, 장르, 국가, 상영시간, 줄거리 가져오기
        try:
            release_date = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[1]/dd').text.strip()
            grade = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[2]/dd').text.strip()
            genre = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[3]/dd').text.strip()
            country = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[4]/dd').text.strip()
            running_time = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[1]/div/div[1]/dl/div[5]/dd').text.strip()
            stroy = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]').text.strip()
        except:
            release_date, grade, genre, country, running_time, stroy = "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"

        # print(f"개봉일: {release_date}\n연령 제한: {grade}\n장르: {genre}\n국가: {country}\n 상영시간: {running_time}")
        # print(f"줄거리: {stroy}")

        # 영화 정보를 딕셔너리로 저장
        movie_info = {
            "제목": title,
            "급상승 순위": rank+"위",
            "장르": genre,
            "개봉일": release_date,
            "상영 시간": running_time,
            "관객수": audience+"만명",
            "관람객 평점": rating,
            "출연진": actors,
            "줄거리": stroy,
            "영화포스터":img_src
        }
        movie_list.append(movie_info)

        # **두 번 뒤로 가기 후, `page`가 2 이상이면 이동**
        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
        # 다음 영화로 이동
        i += 1
    except:
        break

# 결과 출력
print("\n크롤링 완료. 총 수집한 영화 개수:", len(movie_list))
driver.quit()

# 크롤링한 영화 데이터를 JSON 파일로 저장
with open("src/db/movies.json", "w", encoding="utf-8") as f:
    json.dump(movie_list, f, ensure_ascii=False, indent=4)

print("영화 데이터가 movies.json 파일로 저장되었습니다.")

