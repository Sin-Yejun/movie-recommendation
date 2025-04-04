# 최신영화 약 80여개 이상, 오래걸림

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument("--headless")  # GUI 없이 실행
options.add_argument("--disable-gpu")  # GPU 가속 비활성화 (일부 환경에서 필요)
options.add_argument("--window-size=1920x1080")  # 화면 크기 설정

# WebDriver 실행
driver = webdriver.Chrome(options=options)
driver.get('https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%EC%98%81%ED%99%94')
time.sleep(3)

# 현재 페이지 번호 (1부터 시작)
page = 1
i = 1  # 현재 페이지 내 영화 순번
movie_list = []  # 영화 정보를 저장할 리스트
num = 1  # 전체 영화 순번


while True:
    try:
        # 제목, 출연진 가져오기
        time.sleep(3)
        # 영화 제목 가져오기
        title = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{i}]/div[1]/div/div[1]/div/a').text.strip()
        print(f"\n{num}번째 영화 제목: {title}")
        
        # 출연진 가져오기
        actors = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{i}]/div[1]/div/div[2]/dl[3]/dd/span').text.strip()
        print(f"출연진: {actors}")

        # 상세 페이지 클릭
        btn = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{i}]/div[1]/a')
        driver.execute_script("arguments[0].click();", btn)  # JavaScript로 클릭 실행
        time.sleep(3)


        # 순위, 관객 수, 실관람객 평균 평점 가져오기
        try:
            rank = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div/span/em[1]').text.strip()
            audience = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div/span/em[2]').text.strip()
            rating = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]/div/div/div[2]/div/div').text.strip()
        except:
            rank, audience, rating = "N/A", "N/A", "N/A"

        print(f"급상승 순위: {rank}\n관객 수: {audience}\n평균평점: {rating}")

        # 개봉 정보 클릭
        btn = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[1]/div[3]/div/div/ul/li[2]/a')
        btn.click()
        time.sleep(3)

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

        print(f"개봉일: {release_date}, 연령 제한: {grade}, 장르: {genre}, 국가: {country}, 상영시간: {running_time}")
        print(f"줄거리: {stroy}")

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
            "줄거리": stroy
        }
        movie_list.append(movie_info)

        # **두 번 뒤로 가기 후, `page`가 2 이상이면 이동**
        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
        if page >= 2:
            for _ in range(page-1):
                next_button_xpath = '//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[4]/div/a[2]'
                try:
                    next_button = driver.find_element(By.XPATH, next_button_xpath)
                    if next_button.get_attribute("aria-disabled") == "false":
                        ActionChains(driver).move_to_element(next_button).click().perform()
                        time.sleep(3)
                    else:
                        print("더 이상 페이지가 없습니다. 크롤링을 종료합니다.")
                        break
                except:
                    print("다음 페이지 버튼을 찾을 수 없습니다. 크롤링을 종료합니다.")
                    break


        # 다음 영화로 이동
        i += 1
        num += 1
        print(i, page)
    except:
        # 다음 페이지 버튼 처리
        next_button_xpath = '//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[4]/div/a[2]'
        try:
            next_button = driver.find_element(By.XPATH, next_button_xpath)
            if next_button.get_attribute("aria-disabled") == "false":
                ActionChains(driver).move_to_element(next_button).click().perform()
                time.sleep(3)
                i = 1  # 다시 첫 번째 요소부터 검색
                page += 1
            else:
                print("더 이상 페이지가 없습니다. 크롤링을 종료합니다.")
                break
        except:
            print("다음 페이지 버튼을 찾을 수 없습니다. 크롤링을 종료합니다.")
            break

# 결과 출력
print("\n크롤링 완료. 총 수집한 영화 개수:", len(movie_list))
driver.quit()
