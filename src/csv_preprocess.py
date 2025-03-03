import pandas as pd

# csv 파일 불러오기
file_path = "reviews.csv"  # csv 파일의 이름은 영어 이름을 쓰세요
data = pd.read_csv(file_path, encoding="UTF-8")

# 단순하게 쭉 써서 txt 파일로 저장
with open("reviews.txt", "w", encoding="UTF-8") as f:
    for index, row in data.iterrows():
        movie_name = "title : " + row.iloc[0] +'\n'
        rating = "rating : " + str(row.iloc[1]) +'\n'
        review = "review : " + str(row.iloc[2]) +'\n'
        contents = movie_name + rating + review
        f.write(contents + '\n')
