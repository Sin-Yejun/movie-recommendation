from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

lst = []

name = '이매큘레이트'

driver = webdriver.Chrome()
driver.get('https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bkEw&pkid=68&os=34103125&qvt=0&query=%EC%9D%B4%EB%A7%A4%ED%81%98%EB%A0%88%EC%9D%B4%ED%8A%B8%20%EA%B4%80%EB%9E%8C%ED%8F%89')
time.sleep(5)

try:
    btn = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[2]/div[2]/button'))
    )
    btn.click()
    time.sleep(3)
except Exception as e:
    print("버튼 클릭 오류:", e)

scrollable_div = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]'))
)

time.sleep(3)
while True:
    actions = ActionChains(driver)
    actions.move_to_element(scrollable_div).perform()
    time.sleep(1)

    last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)
    driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)
    time.sleep(2)
    new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

    if new_scroll_top == last_scroll_top:
        break

i = 1
last = []

while True:
    try:
        btn = driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[2]/div/button')
        btn.click()
        time.sleep(2)
    except Exception:
        pass
    
    items = scrollable_div.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[2]/div/span[2]')
    scores = scrollable_div.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[1]/div/div[2]')
    
    for j in items:
        item = j.text
    
    for j in scores:
        score = float(j.text.split('\n')[-1])
    
    if last != [score, item]:
        last = [score, item]
        lst.append([name, score, item])
        i += 1
    else:
        break

driver.quit()
print("수집된 데이터 개수:", len(lst))




# """# 플라이 미 투 더 문"""

# name = '플라이 미 투 더 문'

# # 2. 웹 페이지 열기
# driver.get('https://search.naver.com/search.naver?sm=tab_hty.top&where=nexearch&ssc=tab.nx.all&query=%ED%94%8C%EB%9D%BC%EC%9D%B4+%EB%AF%B8+%ED%88%AC+%EB%8D%94+%EB%AC%B8+%EA%B4%80%EB%9E%8C%ED%8F%89&oquery=%EC%9D%B4%EB%A7%A4%ED%81%98%EB%A0%88%EC%9D%B4%ED%8A%B8+%EA%B4%80%EB%9E%8C%ED%8F%89&tqi=ipmPywqptbNssRIhGqlssssssO4-499681')
# time.sleep(5)

# # 3. 스크롤할 특정 요소 찾기
# driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[2]/div[2]/button').click()
# scrollable_div = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]')

# """## 실관람객"""

# while True:
#     actions = ActionChains(driver)
#     actions.move_to_element(scrollable_div).perform()

#     last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)

#     new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     if new_scroll_top == last_scroll_top:
#         break

# i = 1
# last = []

# while True:
#     try:
#         driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[2]/div/button').click()
#     except Exception as e:
#         pass

#     items = scrollable_div.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[2]/div/span[2]')
#     scores = scrollable_div.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[1]/div/div[2]')

#     for j in items:
#         item = j.text

#     for j in scores:
#         score = float(j.text.split('\n')[-1])

#     if last != [score, item]:
#         last = [score, item]
#         lst.append([name, score, item])
#         i += 1
#     else:
#         break

# """## 네티즌"""

# # driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[1]/div/div/ul/li[2]/a').click()
# driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[2]/div[2]/button').click()
# scrollable_div = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]')

# while True:
#     actions = ActionChains(driver)
#     actions.move_to_element(scrollable_div).perform()

#     last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)

#     new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     if new_scroll_top == last_scroll_top:
#         break

# i = 1
# last = []

# while True:
#     try:
#         driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]/ul/li[{i}]/div[2]/div/button').click()
#     except:
#         pass

#     items = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]/ul/li[{i}]/div[2]/div/span')
#     scores = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]/ul/li[{i}]/div[1]/div/div[2]')

#     for j in items:
#         item = j.text

#     for j in scores:
#         score = float(j.text.split('\n')[-1])

#     if last != [score, item]:
#         last = [score, item]
#         lst.append([name, score, item])
#         i += 1
#     else:
#         break

# """## 평론가"""

# # driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[1]/div/div/ul/li[3]/a').click()
# scrollable_div = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div')

# while True:
#     actions = ActionChains(driver)
#     actions.move_to_element(scrollable_div).perform()

#     last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)

#     new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     if new_scroll_top == last_scroll_top:
#         break

# i = 1
# last = []

# while True:
#     try:
#         driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div/ul/li[{i}]/div[3]/button').click()
#     except:
#         pass

#     items = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div/ul/li[{i}]/div[3]/span')
#     scores = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div/ul/li[{i}]/div[2]/div[2]')

#     for j in items:
#         item = j.text

#     for j in scores:
#         score = float(j.text.split('\n')[-1])

#     if last != [score, item]:
#         last = [score, item]
#         lst.append([name, score, item])
#         i += 1
#     else:
#         break

# len(lst)





# """# 탈출"""

# name = '탈출'

# # 2. 웹 페이지 열기
# driver.get('https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bkEw&pkid=68&os=16127542&qvt=0&query=%ED%83%88%EC%B6%9C%3A%20%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8%20%EC%82%AC%EC%9D%BC%EB%9F%B0%EC%8A%A4%20%EA%B4%80%EB%9E%8C%ED%8F%89')
# time.sleep(5)

# # 3. 스크롤할 특정 요소 찾기
# driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[2]/div[2]/button').click()
# scrollable_div = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]')

# """## 실관람객"""

# while True:
#     actions = ActionChains(driver)
#     actions.move_to_element(scrollable_div).perform()

#     last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)

#     new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     if new_scroll_top == last_scroll_top:
#         break

# i = 1
# last = []

# while True:
#     try:
#         driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[2]/div/button').click()
#     except Exception as e:
#         pass

#     items = scrollable_div.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[2]/div/span[2]')
#     scores = scrollable_div.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[1]/div/div[2]')

#     for j in items:
#         item = j.text

#     for j in scores:
#         score = float(j.text.split('\n')[-1])

#     if last != [score, item]:
#         last = [score, item]
#         lst.append([name, score, item])
#         i += 1
#     else:
#         break

# """## 네티즌"""

# # driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[1]/div/div/ul/li[2]/a').click()
# driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[2]/div[2]/button').click()
# scrollable_div = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]')

# while True:
#     actions = ActionChains(driver)
#     actions.move_to_element(scrollable_div).perform()

#     last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)

#     new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     if new_scroll_top == last_scroll_top:
#         break

# i = 1
# last = []

# while True:
#     try:
#         driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]/ul/li[{i}]/div[2]/div/button').click()
#     except:
#         pass

#     items = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]/ul/li[{i}]/div[2]/div/span')
#     scores = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]/ul/li[{i}]/div[1]/div/div[2]')

#     for j in items:
#         item = j.text

#     for j in scores:
#         score = float(j.text.split('\n')[-1])

#     if last != [score, item]:
#         last = [score, item]
#         lst.append([name, score, item])
#         i += 1
#     else:
#         break

# """## 평론가"""

# # driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[1]/div/div/ul/li[3]/a').click()
# scrollable_div = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div')

# while True:
#     actions = ActionChains(driver)
#     actions.move_to_element(scrollable_div).perform()

#     last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)

#     new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     if new_scroll_top == last_scroll_top:
#         break

# i = 1
# last = []

# while True:
#     try:
#         driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div/ul/li[{i}]/div[3]/button').click()
#     except:
#         pass

#     items = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div/ul/li[{i}]/div[3]/span')
#     scores = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div/ul/li[{i}]/div[2]/div[2]')

#     for j in items:
#         item = j.text

#     for j in scores:
#         score = float(j.text.split('\n')[-1])

#     if last != [score, item]:
#         last = [score, item]
#         lst.append([name, score, item])
#         i += 1
#     else:
#         break

# len(lst)





# """# 코난"""

# name = '코난'

# # 2. 웹 페이지 열기
# driver.get('https://search.naver.com/search.naver?where=nexearch&sm=tab_etc&mra=bkEw&pkid=68&os=34212890&qvt=0&query=%EB%AA%85%ED%83%90%EC%A0%95%20%EC%BD%94%EB%82%9C%3A%20100%EB%A7%8C%20%EB%8B%AC%EB%9F%AC%EC%9D%98%20%ED%8E%9C%ED%83%80%EA%B7%B8%EB%9E%A8%20%EA%B4%80%EB%9E%8C%ED%8F%89')
# time.sleep(5)

# # 3. 스크롤할 특정 요소 찾기
# driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[2]/div[2]/button').click()
# scrollable_div = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]')

# """## 실관람객"""

# while True:
#     actions = ActionChains(driver)
#     actions.move_to_element(scrollable_div).perform()

#     last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)

#     new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     if new_scroll_top == last_scroll_top:
#         break

# i = 1
# last = []

# while True:
#     try:
#         driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[2]/div/button').click()
#     except Exception as e:
#         pass

#     items = scrollable_div.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[2]/div/span[2]')
#     scores = scrollable_div.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[4]/div[4]/ul/li[{i}]/div[1]/div/div[2]')

#     for j in items:
#         item = j.text

#     for j in scores:
#         score = float(j.text.split('\n')[-1])

#     if last != [score, item]:
#         last = [score, item]
#         lst.append([name, score, item])
#         i += 1
#     else:
#         break

# """## 네티즌"""

# # driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[1]/div/div/ul/li[2]/a').click()
# driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[2]/div[2]/button').click()
# scrollable_div = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]')

# while True:
#     actions = ActionChains(driver)
#     actions.move_to_element(scrollable_div).perform()

#     last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)

#     new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     if new_scroll_top == last_scroll_top:
#         break

# i = 1
# last = []

# while True:
#     try:
#         driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]/ul/li[{i}]/div[2]/div/button').click()
#     except:
#         pass

#     items = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]/ul/li[{i}]/div[2]/div/span')
#     scores = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[5]/div[4]/ul/li[{i}]/div[1]/div/div[2]')

#     for j in items:
#         item = j.text

#     for j in scores:
#         score = float(j.text.split('\n')[-1])

#     if last != [score, item]:
#         last = [score, item]
#         lst.append([name, score, item])
#         i += 1
#     else:
#         break

# """## 평론가"""

# # driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[1]/div/div/ul/li[3]/a').click()
# scrollable_div = driver.find_element(By.XPATH, '//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div')

# while True:
#     actions = ActionChains(driver)
#     actions.move_to_element(scrollable_div).perform()

#     last_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     driver.execute_script("arguments[0].scrollTop += arguments[0].offsetHeight;", scrollable_div)

#     new_scroll_top = driver.execute_script("return arguments[0].scrollTop;", scrollable_div)

#     if new_scroll_top == last_scroll_top:
#         break

# i = 1
# last = []

# while True:
#     try:
#         driver.find_element(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div/ul/li[{i}]/div[3]/button').click()
#     except:
#         pass

#     items = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div/ul/li[{i}]/div[3]/span')
#     scores = driver.find_elements(By.XPATH, f'//*[@id="main_pack"]/div[3]/div[2]/div/div/div[6]/div/ul/li[{i}]/div[2]/div[2]')

#     for j in items:
#         item = j.text

#     for j in scores:
#         score = float(j.text.split('\n')[-1])

#     if last != [score, item]:
#         last = [score, item]
#         lst.append([name, score, item])
#         i += 1
#     else:
#         break

# len(lst)







# import csv


# header = ['영화 제목', '평점', '리뷰']
# with open('review2.csv', 'w', newline='', encoding='utf-8') as file:
#     writer = csv.writer(file)
#     writer.writerow(header)
#     writer.writerows(lst)

