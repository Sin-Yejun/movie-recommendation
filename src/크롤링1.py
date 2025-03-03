from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
import time

# 영화명 설정
name = '백수아파트'
# 웹 드라이버 실행
driver = webdriver.Chrome()
driver.get('https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bkEw&pkid=68&os=36370805&qvt=0&query=%EB%B0%B1%EC%88%98%EC%95%84%ED%8C%8C%ED%8A%B8%20%EA%B4%80%EB%9E%8C%ED%8F%89')
time.sleep(5)

# 평점 유형별 XPATH 설정
categories = [
    ('실관람객', '//ul/li/a/span[contains(text(), "실관람객")]', '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]'),
    ('네티즌', '//ul/li/a/span[contains(text(), "네티즌")]', '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]'),
    ('평론가', '//ul/li/a/span[contains(text(), "평론가")]', '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div')
]

lst = []

for category, tab_xpath, scroll_xpath in categories:
    print(category,'데이터 수집중...')
    cnt = 0
    # 탭 클릭
    driver.execute_script("window.scrollTo(0, 0);")
    driver.find_element(By.XPATH, tab_xpath).click()
    time.sleep(2)
    
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

        items = driver.find_elements(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[2]/div/span')
        scores = driver.find_elements(By.XPATH, f'{scroll_xpath}/ul/li[{i}]/div[1]/div/div[2]')
        cnt += 1
        for j in items:
            item = j.text
        
        for j in scores:
            score = float(j.text.split('\n')[-1])
        
        if last != [score, item]:
            last = [score, item]
            lst.append([name, category, score, item])
            i += 1
        else:
            break
    print(category,'데이터: ',str(cnt),'수집완료!')
    print()
print(len(lst))
