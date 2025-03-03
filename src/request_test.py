import json
import requests

# 우리가 만든 api를 호출합니다.
url = "http://172.207.35.34:8002/stream_chat/" # url은 자기의 서버 주소를 써야합니다.
message = "영화 추천해주세요."
data = {"content": message}

headers = {"Content-type": "application/json"}

r = requests.post(url, data=json.dumps(data), headers=headers, stream=True)

# API 결과를 print문으로 확인합니다.
for chunk in r.iter_content(1024):
    if chunk:
        decoded_chunk = chunk.decode('utf-8')
        print(decoded_chunk)
