import requests
import pandas as pd
from datetime import datetime, timedelta
import math

import common as common

# 지난달을 yyyy-mm으로 반환
def get_previous_month():
    today = datetime.today()
    first_day_this_month = today.replace(day=1)
    last_day_previous_month = first_day_this_month - timedelta(days=1)
    return last_day_previous_month.strftime("%Y-%m")

# 키워드 가중치에 따라 책 권수를 계산하는 함수
def calculate_books_per_keyword(need_book_count, month):
    # 1. API 요청해서 키워드와 가중치 가져오기
    search_url = f'http://data4library.kr/api/monthlyKeywords?authKey={common.data4library_key}&month={month}&format=json'
    response = requests.get(search_url)
    keyword_list = []  # 키워드와 가중치를 담을 리스트
    for docs in response.json().get("response", {}).get("keywords", []):
        keyword = docs.get("keyword", {}).get("word", "")
        weight = docs.get("keyword", {}).get("weight", 0)
        if keyword:  # 키워드가 비어 있지 않다면 추가
            keyword_list.append((keyword, weight))

    # 2. 총 가중치 계산
    total_weight = sum(weight for _, weight in keyword_list)  # 모든 키워드의 가중치 합산

    # 3. 각 키워드별로 책을 몇 권 추천할지 계산
    books_per_keyword = {}  # 각 키워드별 추천할 책 권수를 저장할 딕셔너리
    for keyword, weight in keyword_list:
        # 가중치를 비율로 변환하여 책 수를 배분
        books_for_keyword = int((weight / total_weight) * need_book_count)
        # 각 책마다 필요한 추가 권수는 더 작은 값으로 조정 (가중치 비율을 더 작게 반영)
        additional_count_per_book = max(1, math.floor(5 / (1 + (weight / total_weight) * 10)))
        books_per_keyword[keyword] = [books_for_keyword, additional_count_per_book]

    # 4. 총 책 수가 필요한 책 수와 정확히 맞지 않을 수 있으므로, 최종 조정
    current_book_count = sum(books[0] for books in books_per_keyword.values())  # 현재 배분된 책 권수 합
    difference = need_book_count - current_book_count  # 차이 계산

    # 5. 남은 책 수를 가중치에 따라 다시 배분
    if difference != 0:
        # 남은 책을 가중치가 높은 키워드에 할당
        sorted_keywords = sorted(keyword_list, key=lambda x: x[1], reverse=True)  # 가중치 높은 순으로 정렬
        for i in range(abs(difference)):
            keyword = sorted_keywords[i % len(sorted_keywords)][0]  # 순차적으로 가중치가 큰 키워드에 추가
            books_per_keyword[keyword][0] += 1  # 필요한 책 권수 증가

    # 6. 각 키워드의 총 권수 계산 (필요한 책 권수 × 각 책의 추가 권수)
    total_books_per_keyword = {
        key: [value[0], value[0] * value[1]] for key, value in books_per_keyword.items()
    }

    return total_books_per_keyword, keyword_list  # 계산된 책 권수와 키워드 리스트 반환

# API 호출을 수행하는 공통 함수
def fetch_books_from_api(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # 요청 실패 시 예외 발생
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API 요청 오류: {e}")
        return None

def get_books_count(books_needed):
    if not books_needed:
        return []
    max_results_per_page = 100
    total_pages = (books_needed // max_results_per_page) + 1  
    book_data = []  # 책 정보를 저장할 리스트   
    page = 1
    while len(book_data) < books_needed:
        
        search_url = f'http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey={common.aladin_key}&QueryType=ItemNewSpecial&MaxResults={max_results_per_page}&Start={page}&SearchTarget=Book&output=js&Version=20131101'
        response = fetch_books_from_api(search_url)
        result = response.get("item")
        
        for book in result:
            if any(k in book.get("categoryName", "") for k in common.aladin_exclude_keywords):
                continue

            book_info = {
                'ISBN'  : book.get("isbn13"),
                '상품명'  :book.get("title"),
                '저자'   : book.get("author"),
                '출판사'  : book.get("publisher"),
                '분야'   : book.get("categoryName"),
            }
            book_data.append(book_info)
        page+=1
    return book_data

# 책 정보를 가져오는 함수
def get_books_for_keyword(keyword, books_needed):
    if not books_needed:
        return [], False
    
    max_results_per_page = min(books_needed, 100)
    total_pages = (books_needed // max_results_per_page) + 1 if books_needed > 100 else 1
    
    book_data = []  # 책 정보를 저장할 리스트
    for page in range(1, total_pages + 1):
        search_url = f'http://www.aladin.co.kr/ttb/api/ItemSearch.aspx?ttbkey={common.aladin_key}&Query={keyword}&QueryType=Keyword&MaxResults={max_results_per_page}&Start={page}&SearchTarget=Book&output=js&Version=20131101'
        result = fetch_books_from_api(search_url)
        
        if result:
            for book in result.get("item", []):
                if any(k in book.get("categoryName", "") for k in common.aladin_exclude_keywords):
                    continue

                book_info = {
                    'ISBN': book.get("isbn13"),
                    '상품명': book.get("title"),
                    '저자': book.get("author"),
                    '출판사': book.get("publisher"),
                    '분야': book.get("categoryName"),
                }
                book_data.append(book_info)
                if len(book_data) >= books_needed:
                    break
    return book_data, False

# 책 데이터를 CSV 파일로 저장하는 함수
def save_books_to_csv(book_data, file_path, need_book_count):
    result_df = pd.DataFrame(book_data)
    
    # 숭실대 도서 제거
    exclusion_df = pd.read_csv(f"{common.resource_file_path}/books_with_count.csv")  # 숭실대 도서
    exclusion_df = exclusion_df[exclusion_df['권수'] > 8]
    result_df = result_df[~result_df['ISBN'].isin(exclusion_df['ISBN'])]
    
    # ISBN별 개수를 "권수" 컬럼에 추가
    result_df["권수"] = result_df.groupby("ISBN")["ISBN"].transform("count")

    # 중복된 ISBN을 하나로 합치고, 첫 번째 책 정보만 남김
    result_df = result_df.drop_duplicates(subset=["ISBN"], keep="first")
    
    # 누적 권수를 계산하면서 need_book_count권까지 선택
    result_df["누적권수"] = result_df["권수"].cumsum()
    result_df = result_df[result_df["누적권수"] <= need_book_count]

    # 필요 없어진 "누적권수" 컬럼 삭제
    # result_df.drop(columns=["누적권수"], inplace=True)
    
    # csv로 저장
    result_df.to_csv(file_path, index=False, encoding='utf-8')  # UTF-8 인코딩으로 저장

# 주 실행 부분
def main(need_book_count):
    # 1.키워드와 각 키워드별로 추천할 책 수 계산
    books_per_keyword, keyword_list = calculate_books_per_keyword(need_book_count, get_previous_month())
    print("1단계 끝\n")
    
    # 2. 뒤에서부터 키워드를 검색하여 책 정보를 가져오기
    book_data = []  # 책 데이터를 저장할 리스트
    for i in range(len(keyword_list) - 1, -1, -1):  # 뒤에서부터 키워드를 하나씩 처리
        print(f"{len(keyword_list)} / {len(keyword_list) - i}")
        keyword = keyword_list[i][0]  # 키워드 추출
        books_needed = books_per_keyword[keyword][0]  # 해당 키워드에 배정된 책 권수
        
        # 책 정보를 가져옴
        books, no_books = get_books_for_keyword(keyword, books_needed)
        if no_books:
            # 책이 없으면 이전 키워드로 권수 증가
            if i > 0:
                next_keyword = keyword_list[i - 1][0]
                books_per_keyword[next_keyword][0] += 1
        else:
            book_data.extend(books)  # 책 정보를 book_data 리스트에 추가

    print("2단계 끝\n")
    change_book_needed_count = need_book_count - len(book_data) if len(book_data) < need_book_count else 0
    
    # 3. 부족한 도서 채우기
    books = get_books_count(change_book_needed_count)
    book_data.extend(books)
    print("3단계 끝\n")
    
    # 4. 책 데이터를 CSV로 저장
    save_books_to_csv(book_data, f"{common.save_file_path}/keyword_book_recommendations.csv", need_book_count)

# 실행
if __name__ == "__main__":
    main(4000)