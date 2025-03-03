from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

# 웹 드라이버 실행
driver = webdriver.Chrome()
driver.get('https://search.naver.com/search.naver?where=nexearch&sm=top_hty&fbm=0&ie=utf8&query=%EC%98%81%ED%99%94')
time.sleep(5)

i = 1
num = 1
movie_list = []

while True:
    xpath = f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{i}]'
    
    try:
        # 영화 제목
        title_element = driver.find_element(By.XPATH, f'{xpath}/div[1]/div/div[1]/div/a')
        title = title_element.text.strip()

        # 개요 (장르)
        try:
            genre = driver.find_element(By.XPATH, f'{xpath}/div[1]/div/div[2]/dl[1]/dd').text.strip()
        except:
            genre = None

        # 상영 시간
        try:
            duration = driver.find_element(By.XPATH, f'{xpath}/div[1]/div/div[2]/dl[1]/dd[2]').text.strip()
            if "분" not in duration:
                duration = None
        except:
            duration = None

        # 개봉 날짜
        try:
            release_date = driver.find_element(By.XPATH, f'{xpath}/div[1]/div/div[2]/dl[2]/dd').text.strip()
        except:
            release_date = None
        # 출연진
        try:
            actors = driver.find_element(By.XPATH, f'{xpath}/div[1]/div/div[2]/dl[3]/dd').text.strip()
        except:
            actors = None

        # 평점
        try:
            rating = driver.find_element(By.XPATH, f'{xpath}/div[1]/div/div[2]/dl[2]/dd[2]/span[@class="num"]').text.strip()
        except:
            rating = None

        # 데이터 저장
        movie_info = {
            "번호": num,
            "제목": title,
            "장르": genre,
            "상영 시간": duration,
            "개봉일": release_date,
            "출연진":actors,
            "평점": rating
        }
        movie_list.append(movie_info)
        print(movie_info)

        i += 1
        num += 1

    except:
        # 다음 페이지 버튼 처리
        next_button_xpath = '//a[@class="pg_next on _next"]'

        try:
            next_button = driver.find_element(By.XPATH, next_button_xpath)

            if next_button.get_attribute("aria-disabled") == "false":
                ActionChains(driver).move_to_element(next_button).click().perform()
                time.sleep(2)
                i = 1  # 다시 첫 번째 요소부터 검색
            else:
                print("더 이상 페이지가 없습니다. 크롤링을 종료합니다.")
                break

        except:
            print("다음 페이지 버튼을 찾을 수 없습니다. 크롤링을 종료합니다.")
            break

# 브라우저 종료
driver.quit()
