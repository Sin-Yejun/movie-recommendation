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
xpath = f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div/div[1]/div[1]/div[{i}]'
while True:
    try:
        # 영화 제목
        title_element = driver.find_element(By.XPATH, f'{xpath}/div[1]/div/div[1]/div/a')
        title = title_element.text.strip()
        print("영화제목: ",title)
        btn = driver.find_element(By.XPATH, f'{xpath}/div[1]/a[1]')
        btn.click()
        time.sleep(3)
        # 순위 가져오기
        rank = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div/span/em[1]').text.strip()

        # 관객 수 가져오기
        audience = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div[2]/div/div[2]/div/div/div[1]/div/div/span/em[2]').text.strip()

        print(f"순위: {rank}, 관객 수: {audience}")
        btn = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[1]/div[3]/div/div/ul/li[2]/a')
        btn.click()
        time.sleep(3)
        break
    except: 
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
