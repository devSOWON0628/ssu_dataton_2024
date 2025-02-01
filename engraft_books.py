import pandas as pd
import requests

import common as common

def clear_df(dataframe):
    # 숭실대에 이미 포함되어 있는 도서의 경우 삭제
    exclusion_df = pd.read_csv(f"{common.resource_file_path}/books_with_count.csv", low_memory=False)
    exclusion_df = exclusion_df[exclusion_df['권수'] > 8]
    dataframe = dataframe[~dataframe['ISBN'].isin(exclusion_df['ISBN'])]
    
    # 이미 데이터프레임에 있는 도서라면 머지후 권수 추가
    merged_books = dataframe.groupby(['ISBN'], as_index=False).agg({
        '상품명': 'first',
        '저자': 'first',
        '출판사': 'first',
        '분야': 'first',
        '권수': 'sum'
    })
    merged_books["권수"] = merged_books["권수"].apply(lambda x: 8 if x >= 8 else x)
    
    # 누적 권수 개산
    merged_books["누적권수"] = merged_books["권수"].cumsum()
    
    print(merged_books.tail(1).iloc[0]["누적권수"])  
    return merged_books
    
def fill_books(dataframe, needed_book_count):
    count = 1
    no_data_count = 0
    while dataframe.tail(1).iloc[0]["누적권수"] <= needed_book_count:
        # URL 목록 정의
        search_urls = [
            f'http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey={common.aladin_key}&QueryType=ItemNewAll&MaxResults=50&Start={count}&SearchTarget=Book&output=js&Version=20131101', # 1000
            f'http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey={common.aladin_key}&QueryType=Bestseller&MaxResults=50&Start={count}&SearchTarget=Book&output=js&Version=20131101', # 1000
            f'http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey={common.aladin_key}&QueryType=BlogBest&MaxResults=50&Start={count}&SearchTarget=Book&output=js&Version=20131101', # 100
            f'http://www.aladin.co.kr/ttb/api/ItemList.aspx?ttbkey={common.aladin_key}&QueryType=ItemNewSpecial&MaxResults=50&Start={count}&SearchTarget=Book&output=js&Version=20131101' # 1905
        ]

        if no_data_count>= 4:
            break
        else:
            no_data_count = 0
            
        # 각 URL에 대해 데이터를 요청하고 책 데이터를 추가
        for url in search_urls:
            response = requests.get(url)
            result = response.json().get("item", [])
            # 카테고리 키워드 필터링
            book_data = []
            if len(result) <= 0 or 1000 < count*50:
                no_data_count+=1
                continue
            # print(len(result), result[0].get("title"), result[0].get("categoryName"), response.json().get("totalResults"), count*50)
            for book in result:
                if any(k in book.get("categoryName", "") for k in common.aladin_exclude_keywords):
                    continue
                book_info = {
                    'ISBN': book.get("isbn13"),
                    '상품명': book.get("title"),
                    '저자': book.get("author"),
                    '출판사': book.get("publisher"),
                    '분야': book.get("categoryName"),
                    '권수': 1  # 기본적으로 권수는 1로 설정
                }
                book_data.append(book_info)

            # 새로운 데이터가 있으면 DataFrame에 추가
            if book_data:
                df_aladin = pd.DataFrame(book_data)
                dataframe = pd.concat([dataframe, df_aladin], ignore_index=True)
            
            # 데이터프레임을 정리하고 권수를 합산
            dataframe = clear_df(dataframe)
        count += 1
    
    # 누리 api
    if dataframe.tail(1).iloc[0]["누적권수"] <= needed_book_count:
        page = 1
        while dataframe.tail(1).iloc[0]["누적권수"] <= needed_book_count:
            search_url = f'http://data4library.kr/api/loanItemSrch/?authKey={common.data4library_key}&format=json&to_age=40&from_age=20&pageNo={page}'
            response = requests.get(search_url)
            book_data = []  # 키워드와 가중치를 담을 리스트
            for docs in response.json().get("response", {}).get("docs", []):
                book_info = {
                    'ISBN': docs.get("doc").get("isbn13"),
                    '상품명': docs.get("doc").get("bookname"),
                    '저자': docs.get("doc").get("authors"),
                    '출판사': docs.get("doc").get("publisher"),
                    '분야': docs.get("doc").get("class_nm"),
                    '권수': 1  # 기본적으로 권수는 1로 설정
                }
                book_data.append(book_info)
            if book_data:
                df_naru = pd.DataFrame(book_data)
                dataframe = pd.concat([dataframe, df_naru], ignore_index=True)
            
            # 데이터프레임을 정리하고 권수를 합산
            dataframe = clear_df(dataframe)
            
            page +=1
    return dataframe

def delete_all_files():
    common.file_delete(f'{common.save_file_path}/new_book_recommendations.csv')
    common.file_delete(f'{common.save_file_path}/bestseller_book_recommendations.csv')
    common.file_delete(f'{common.save_file_path}/keyword_book_recommendations.csv')
    common.file_delete(f'{common.save_file_path}/genre_book_recommendations.csv')
    
def main(needed_input):        
    new_books       = pd.read_csv(f'{common.save_file_path}/new_book_recommendations.csv')
    best_books      = pd.read_csv(f'{common.save_file_path}/bestseller_book_recommendations.csv')
    keyword_books   = pd.read_csv(f'{common.save_file_path}/keyword_book_recommendations.csv')
    genre_books     = pd.read_csv(f'{common.save_file_path}/genre_book_recommendations.csv')

    # 4개의 데이터프레임 합치기
    merged_books = pd.concat([new_books, best_books, keyword_books, genre_books], ignore_index=True)

    # ISBN을 기준으로 권수 합치기
    merged_books = merged_books.groupby(['ISBN'], as_index=False).agg({
        '상품명': 'first',
        '저자': 'first',
        '출판사': 'first',
        '분야': 'first',
        '권수': 'sum'
    })
    merged_books["권수"] = merged_books["권수"].apply(lambda x: 8 if x >= 8 else x)
    merged_books["누적권수"] = merged_books["권수"].cumsum()

    result_df = fill_books(merged_books, needed_input) # 추가 추천 진행
    result_df = result_df.sort_values(by='권수', ascending=False).reset_index(drop=True)
    result_df["누적권수"] = result_df["권수"].cumsum()
    result_df = result_df[result_df["누적권수"] <= needed_input]
    
    result_df.to_csv(f'{common.get_download_path()}/combined_book_recommendations.csv', index=False, encoding='utf-8')
    delete_all_files() # 4개 엑셀 목록 삭제

# 실행
if __name__ == "__main__":
    main(20000)