# 최신 영화 8개

import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.chrome.options import Options
import pandas as pd

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

# 원격 브라우저 (Docker용)
selenium_url = os.getenv("SELENIUM_URL", "http://selenium:4444/wd/hub")
driver = webdriver.Remote(command_executor=selenium_url, options=options)

# 크롤링 시작
driver.get("https://search.naver.com/search.naver?query=영화")
time.sleep(2)

k = 1  # 현재 페이지 내 영화 순번
reviews = []  # 영화 리뷰를 저장할 리스트
categories = [
    ('실관람객', '//ul/li/a/span[contains(text(), "실관람객")]', '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]'),
    ('네티즌', '//ul/li/a/span[contains(text(), "네티즌")]', '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]'),
    ('평론가', '//ul/li/a/span[contains(text(), "평론가")]', '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div')
]

while True:
    try:
        # 영화 제목 가져오기
        title = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{k}]/div[1]/div/div[1]/div/a').text.strip()
        print(f"\n{k}번째 영화 제목: {title}")

        # 상세 페이지 클릭
        btn = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{k}]/div[1]/a')
        driver.execute_script("arguments[0].click();", btn)  # JavaScript로 클릭 실행
        time.sleep(1)

        # 관람평 메뉴 클릭
        driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[1]/div[3]/div/div/ul/li[5]/a').click()
        time.sleep(1)

        idx = 4
        for category, tab_xpath, scroll_xpath in categories:
            print(category,'데이터 수집중...')
            cnt = 0
            # 탭 클릭
            driver.execute_script("window.scrollTo(0, 0);")
            driver.find_element(By.XPATH, tab_xpath).click()
            time.sleep(5)
            
            # 스포일러 토글 누르기
            if idx < 6:
                # XPATH를 사용하여 버튼 요소 찾기
                button = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[{idx}]/div[2]/div[2]/button/span[1]')
                driver.execute_script("arguments[0].click();", button)
                time.sleep(3)
                idx += 1

            # 스크롤 가능한 영역 찾기
            scrollable_div = driver.find_element(By.XPATH, scroll_xpath)
            
            # 스크롤 끝까지 내리기
            while True:
                actions = ActionChains(driver)
                actions.move_to_element(scrollable_div).perform()
                last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
                driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)
                new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
                if new_scroll_top == last_scroll_top:
                    break

            # 리뷰 크롤링
            i = 1
            last = []
            while True:
                try:
                    driver.find_element(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[2]/div/button').click()
                except:
                    pass
       
                if category == '평론가':
                    items = driver.find_elements(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[3]/span')
                else:
                    items = driver.find_elements(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[2]/div/span')
                
                scores = driver.find_elements(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[1]/div/div[2]')
                cnt += 1
                for j in items:
                    item = j.text
                
                for j in scores:
                    score = float(j.text.split('\n')[-1])
                
                if last != [score, item]:
                    last = [score, item]
                    reviews.append([title, category, score, item])
                    i += 1
                else:
                    break

        k += 1
        driver.back()
        time.sleep(0.5)
        driver.back()
        time.sleep(0.5)
    except:
        print(f"{k} 페이지 오류")
        break

# 데이터 프레임 생성
df = pd.DataFrame(reviews, columns=['제목', '작성자유형', '평점', '리뷰'])

# CSV 파일로 저장
df.to_csv('src/db/movie_reviews.csv', index=False, encoding='utf-8-sig')

print("CSV 파일 저장 완료: movie_reviews.csv")