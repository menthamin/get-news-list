import os
import requests
import pandas as pd
from dateutil.parser import parse
import datetime
from tqdm import tqdm
from bs4 import BeautifulSoup
from dotenv import load_dotenv


# Naver Search API Key
load_dotenv()
client_id = os.environ.get("client_id")
client_secret = os.environ.get("client_secret")
url = "https://openapi.naver.com/v1/search/news.json"
headers = {
    "X-Naver-Client-Id": client_id,
    "X-Naver-Client-Secret": client_secret
}

words_list = ["하나대체", "하나 대체"]
# words_list = ["아리사"]

KST = datetime.timezone(datetime.timedelta(hours=9))
now_date_obj = datetime.datetime.combine(datetime.date.today(), datetime.datetime.min.time(), tzinfo=KST)
now_date_obj = now_date_obj - datetime.timedelta(days=5, hours=0)
now_date_str = datetime.datetime.strftime(now_date_obj, "%Y%m%d%H%M")
print(now_date_str)
"""
날짜 사용 케이스
now_date_obj = now_date_obj - datetime.timedelta(days=0, hours=6)  # days=0, hours=6: 전일 18시 이후
now_date_obj = now_date_obj - datetime.timedelta(days=0, hours=0)  # days=0, hours=0: 당일 00시 이후
"""


for word in words_list:

    df = pd.DataFrame()

    for page in tqdm(range(1, 101)):
        params = {
            "query": word,  # 네이버 기사 검색 값
            "display": "100",  # 페이지당 출력 개수: 범위 1~100
            "start": page,  # 페이지 번호: 범위 1~100(최대 100페이지 까지 조회 가능)
            "sort": "sim"  # sort: sim: 정확도순 정렬(기본), date: 날짜순 정렬
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        temp_df = pd.DataFrame(data["items"])
        temp_df.pubDate = [parse(pub_date) for pub_date in temp_df.pubDate]
        temp_df = temp_df[temp_df.pubDate >= now_date_obj]
        df = pd.concat([df, temp_df])

    filtered_df = df[df["title"].str.contains(word) | df["description"].str.contains(word)]
    save_columns_list = ["title", "description", "originallink", "pubDate"]
    rename_columns_dict = {
        "title": "제목",
        "description": "본문",
        "originallink": "url",
        "pubDate": "발행일"
    }

    filtered_df = filtered_df[save_columns_list]
    filtered_df.title = [BeautifulSoup(title).text for title in filtered_df.title]
    filtered_df.description = [BeautifulSoup(description).text for description in filtered_df.description]  # html.unescape(text)
    filtered_df.rename(columns=rename_columns_dict, inplace=True)
    filtered_df.drop_duplicates(inplace=True)
    filtered_df.sort_values(by=["발행일"], ascending=False, inplace=True)

    filtered_df.to_csv(f"news_data/{now_date_str}_{word}.csv", index=False, encoding="utf8")