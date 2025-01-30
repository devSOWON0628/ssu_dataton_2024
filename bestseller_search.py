from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os
import warnings
import requests

import common as common

warnings.filterwarnings("ignore")
NEEDED_MONTHS = 36  # 최근 3년

# 월 단위 계산 함수
def calc_year_month(before_month):
    target_date = datetime.today() - relativedelta(months=before_month)
    return target_date.year, f"{target_date.month:02d}"

# 데이터프레임 필터링 함수
def filter_dataframe(df, columns, rename_mapping):
    return df[columns].rename(columns=rename_mapping)

# YES24 베스트셀러 크롤링
def get_best_books_by_yes24(chrome_options):
    dataframes = []
    browser = webdriver.Chrome(options=chrome_options)
    try:
        for i in range(NEEDED_MONTHS):
            try:
                print(f"{NEEDED_MONTHS}/{i + 1}")
                year, month = calc_year_month(i)
                url = f"https://www.yes24.com/Product/Category/MonthWeekBestSeller?categoryNumber=001&pageSize=300&type=month&saleYear={year}&saleMonth={month}"
                browser.get(url)
                browser.fullscreen_window()
                WebDriverWait(browser, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bestContentsWrap"]/div[3]/div[2]/a[5]'))).click()
                time.sleep(2)
                
                file_name = f"{common.get_download_path()}/예스24_국내도서_월별+베스트_{datetime.today().strftime('%Y-%m-%d')}.xlsx"
                df = pd.read_excel(file_name)
                common.file_delete(file_name)
                df_filtered = filter_dataframe(df, ['ISBN', '상품명', '저자', '출판사', '관리분류'], {'관리분류': '분야'})
                dataframes.append(df_filtered)
            except:
                continue
    finally:
        browser.quit()
    return dataframes

# 교보문고 베스트셀러 크롤링
def get_best_books_by_kyobo(chrome_options):
    dataframes = []
    browser = webdriver.Chrome(options=chrome_options)
    try:
        for i in range(NEEDED_MONTHS):
            print(f"{NEEDED_MONTHS}/{i + 1}")
            year, month = calc_year_month(i+1)
            url = f"https://store.kyobobook.co.kr/bestseller/total/monthly?page=1&ymw={year}{month}&per=200"
            browser.get(url)
            browser.fullscreen_window()
            WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[1]/main/section/div/div/section/div[4]/div/div/button[3]'))).click()
            
            for retry_count in range(5):
                try:
                    time.sleep(2)
                    file_name = f"{common.get_download_path()}/교보문고_종합_베스트셀러_상품리스트.xlsx"
                    df = pd.read_excel(file_name)
                    break
                except:
                    time.sleep(6)
            
            common.file_delete(file_name)
            df_filtered = filter_dataframe(df, ['상품코드', '상품명', '인물', '출판사', '분야'], {'상품코드': 'ISBN', '인물': '저자'})
            dataframes.append(df_filtered)
    finally:
        browser.quit()
    return dataframes

# 알라딘 베스트셀러 API 호출
def get_best_books_by_aladin():
    dataframes = []
    for i in range(NEEDED_MONTHS):
        print(f"{NEEDED_MONTHS}/{i + 1}")
        url = f"http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey={common.aladin_key}&QueryType=Bestseller&MaxResults=100&Start={i+1}&SearchTarget=Book&output=js&Version=20131101"
        response = requests.get(url)
        result = response.json().get("item", [])
        
        book_data = [
            { 
             'ISBN': book.get("isbn13"), 
             '상품명': book.get("title"), 
             '저자': book.get("author"), 
             '출판사': book.get("publisher"), 
             '분야': book.get("categoryName") 
            }
            for book in result if not any(k in book.get("categoryName", "") for k in common.aladin_exclude_keywords)
        ]
        dataframes.append(pd.DataFrame(book_data))
    return dataframes

# 데이터 처리 및 저장
def process_and_save_data(dataframes, output_file, exclusion_file, needed_count):
    final_df = dataframes
    exclusion_df = pd.read_csv(exclusion_file)
    final_df = final_df[~final_df['ISBN'].isin(exclusion_df['ISBN'])]
    
    exclude_categories = ["유아", "어린이", "만화"]
    final_df = final_df[~final_df["분야"].str.contains('|'.join(exclude_categories), na=False)]
    
    final_df["권수"] = final_df.groupby("ISBN")["ISBN"].transform("count")
    final_df = final_df.drop_duplicates(subset=["ISBN"], keep="first")
    final_df["누적권수"] = final_df["권수"].cumsum()
    final_df = final_df[final_df["누적권수"] <= needed_count]
    
    final_df.to_csv(output_file, index=False, encoding='utf-8')

# 메인 함수
def main(bestseller_needed_count):
    chrome_options = common.get_chrome_options()
    
    print("알라딘 시작")
    aladin_data = pd.concat(get_best_books_by_aladin(), ignore_index=True)

    print("교보 시작")
    kyobo_data = pd.concat(get_best_books_by_kyobo(chrome_options), ignore_index=True)

    print("yes24 시작")
    yes24_data = pd.concat(get_best_books_by_yes24(chrome_options), ignore_index=True)

    print("저장")
    final_df = pd.concat([aladin_data, kyobo_data, yes24_data], ignore_index=True)
    
    process_and_save_data(
        final_df,
        output_file=f"{common.save_file_path}/bestseller_book_recommendations.csv",
        exclusion_file=f"{common.resource_file_path}/book_data.csv",
        needed_count=bestseller_needed_count
    )
    
# 실행
if __name__ == "__main__":
    main(4000)