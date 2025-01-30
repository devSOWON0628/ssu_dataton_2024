from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
import datetime
import shutil
import os
import xml.etree.ElementTree as ET
import pandas as pd
import warnings
import requests
warnings.filterwarnings("ignore")

import common as common

# Constants
NEEDED_WEEKS = 36  # 최근 6개월
MAX_RETRIES = 5

def get_file_to_temp():
    return f"{common.get_download_path()}/예스24_국내도서_주목할+신상품_{datetime.date.today().strftime('%Y-%m-%d')}"

def cacl_year_month_week_before(before_week):
    today = datetime.date.today()
    delta = datetime.timedelta(weeks=before_week)
    target_date = today - delta
    year = target_date.year
    month = target_date.month

    # 해당 날짜가 몇 번째 주에 속하는지 계산 (6주 기준)
    first_day_of_month = datetime.date(year, month, 1)  # 해당 월의 첫 번째 날
    days_diff = (target_date - first_day_of_month).days  # 첫 날부터 며칠 차이인지 계산
    week = (days_diff // 7) + 1  # 6주 기준으로 주차 계산

    # 만약 주차가 6주를 넘어가면 다음 달로 넘어가지 않도록 조정
    if week > 6:
        week = 6

    # 월과 주차를 두 자리 형식으로 반환
    month = f"{month:02d}"  # 월은 두 자리 형식으로 유지
    return year, month, week

def get_new_books_by_aladin():
    print("알라딘 신간 검색 시작")
    dataframes = []
    book_data = []  # 책 정보를 저장할 리스트
    for i in range(NEEDED_WEEKS):
        print(f"{NEEDED_WEEKS}/{i+1}")
        search_url = f'http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey={common.aladin_key}&QueryType=ItemNewSpecial&MaxResults=100&Start={i+1}&SearchTarget=Book&output=js&Version=20131101'
        response = requests.get(search_url)
        result = response.json().get("item")
        for book in result:
            if any(k in book.get("categoryName", "") for k in common.aladin_exclude_keywords):
                continue

            book_info = {
                'ISBN'  : book.get("isbn13"),
                '상품명'  :book.get("title"),
                '저자'   : book.get("author"),
                '출판사'  : book.get("publisher"),
                '분야'   : book.get("categoryName")
            }
            book_data.append(book_info)
            
    dataframes.append(pd.DataFrame(book_data))
    return dataframes

def get_new_books_by_yes24():
    print("yes24 신간 검색 시작")
    dataframes = []
    browser = webdriver.Chrome(options=common.get_chrome_options())
    
    for i in range(NEEDED_WEEKS):
        try:
            print(f"{NEEDED_WEEKS}/{i+1}")
            url = f"https://www.yes24.com/Product/Category/AttentionNewProduct?categoryNumber=001001&pageNumber={i+1}&pageSize=120&newProductType=ATTENTION&viewMode=list&sortTp=02"
            browser.get(url)
            browser.fullscreen_window()
            WebDriverWait(browser, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="newProductContentsWrap"]/div[3]/div[2]/a[5]'))).click()
            
            time.sleep(2)
            
            try:
                if not os.path.exists(f"{get_file_to_temp()}.xlsx"):  # 파일 존재 여부 확인
                    raise FileNotFoundError(f"파일을 찾을 수 없습니다")
                df = pd.read_excel(f"{get_file_to_temp()}.xlsx")
                common.file_delete(f"{get_file_to_temp()}.xlsx")
                df.columns = ['ISBN', '상품번호', '상품명', '판매가', 'YES포인트', '저자', '출판사', '설명', '출고예상일', '관리분류']
                df_filtered = df[['ISBN', '상품명', '저자', '출판사', '관리분류']]
                df_filtered.rename(columns = {'관리분류' : '분야'}, inplace=True)
                dataframes.append(df_filtered)
            except FileNotFoundError as e:
                print(f"파일을 찾을 수 없습니다. for문을 끝냅니다.")
                break
        except:
            continue;
        finally:
            browser.quit()
        
    # print("yes24 신간 검색 종료\n")
    return dataframes

def get_new_books_by_kyobo():
    print("교보 신간 검색 시작")
    dataframes = []
    browser = webdriver.Chrome(options=common.get_chrome_options())
    
    for i in range(NEEDED_WEEKS):
        print(f"{NEEDED_WEEKS}/{i+1}")
        year, month, week = cacl_year_month_week_before(i)
        for retry_count in range(MAX_RETRIES):
            try:
                url = f"https://product.kyobobook.co.kr/new/KOR#?page=1&sort=new&year={year}&month={month}&week={week}&per=20&saleCmdtDvsnCode=KOR&gubun=newGubun&saleCmdtClstCode="
                browser.get(url)
                browser.fullscreen_window()
                WebDriverWait(browser, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="excelDown"]'))).click()
                # print("다운로드 성공")
                break
            except Exception as e:
                print(f"오류 발생: ({retry_count + 1}/{MAX_RETRIES})")
                time.sleep(2)
            else:
                print("최대 시도 횟수 초과. 다운로드를 할 수 없습니다.")
                return
        
        
        for retry_count in range(MAX_RETRIES):
            try:
                time.sleep(3)
                df = pd.read_excel(f"{common.get_download_path()}/교보문고_신상품_상품리스트.xlsx")
                break
            except Exception as e:
                print(f"오류 발생: ({retry_count + 1}/{MAX_RETRIES})")
                time.sleep(6)
            else:
                print("최대 시도 횟수 초과. 파일을 읽을 수 없습니다.")
                return
        
        common.file_delete(f"{common.get_download_path()}/교보문고_신상품_상품리스트.xlsx")
        df.columns = ['순번', '상품코드', '판매상품ID', '상품명', '정가', '판매가', '할인율', '적립율', '적립예정포인트', '인물', '출판사', '발행(출시)일자', '분야']
        
        df_filtered = df[['상품코드', '상품명', '인물', '출판사', '분야']]
        df_filtered.rename(columns = {'상품코드' : 'ISBN', '인물' : '저자'}, inplace=True)
        dataframes.append(df_filtered)
        
    browser.quit()
    return dataframes
    # print("교보 신간 검색 종료\n")

def main(new_needed_count):
    # 교보에서 데이터를 수집
    kyobo_data = pd.concat(get_new_books_by_kyobo(), ignore_index=True)
    aladin_data = pd.concat(get_new_books_by_aladin(), ignore_index=True)
    yes24_data = pd.concat(get_new_books_by_yes24(), ignore_index=True)

    # 모든 데이터를 합침
    final_df = pd.concat([kyobo_data, aladin_data, yes24_data], ignore_index=True)

    # ISBN별 개수를 "권수" 컬럼에 추가
    final_df["권수"] = final_df.groupby("ISBN")["ISBN"].transform("count")

    # 중복된 ISBN을 하나로 합치고, 첫 번째 책 정보만 남김
    final_df = final_df.drop_duplicates(subset=["ISBN"], keep="first")

    # 이미 숭실대학교가 가지고 있는 도서의 경우 제외
    ssu_df = pd.read_csv(f'{common.resource_file_path}/books_with_count.csv')
    ssu_df = ssu_df[ssu_df['권수'] > 8]
    final_df = final_df[~final_df['ISBN'].isin(ssu_df['ISBN'])] 

    # 유아, 어린이, 만화 도서 제외
    final_df = final_df[~final_df["분야"].str.contains("유아", na=False)]
    final_df = final_df[~final_df["분야"].str.contains("어린이", na=False)]
    final_df = final_df[~final_df["분야"].str.contains("만화", na=False)]

    # 누적 권수를 계산하면서 4000권까지 선택
    final_df["누적권수"] = final_df["권수"].cumsum()
    final_df = final_df[final_df["누적권수"] <= new_needed_count]

    # 필요 없어진 "누적권수" 컬럼 삭제
    # final_df = final_df.drop(columns=["누적권수"])

    final_df.to_csv(f'{common.save_file_path}/new_book_recommendations.csv', index=False, encoding='utf-8')
    
# 실행
if __name__ == "__main__":
    main(4000)