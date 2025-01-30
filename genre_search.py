import pandas as pd

import common as common

# 150 아시아철학
# 800 문학
# 230 기독교 
# 690 오락 및 스포츠
# 180 심리학
# 910 아시아 역사
# 700 언어학
# 740 영어
# 500 공학
# 160  서양 철학
kdc_list = [150, 800, 230, 690, 180, 910, 700, 740, 500, 160]

# 데이터 로드 및 초기 정렬
# 순위,서명,저자,출판사,출판년도,권,ISBN,ISBN부가기호,KDC,대출건수,year,month,포괄 장르,상세 장르

# ssu 도서관 데이터 제거
def exclude_ssu_data(dataframe):
    exclusion_df = pd.read_csv(f'{common.resource_file_path}/book_data.csv')
    dataframe = dataframe[~dataframe['ISBN'].isin(exclusion_df['ISBN'])]
    return dataframe

def main(needed_input):
    book_list = []
    result_df = pd.read_csv(f'{common.resource_file_path}/analysis_book_genre_Trendy1.csv', low_memory=False)
    result_df = result_df.sort_values(by="대출건수", ascending=False)
    result_df = result_df.drop_duplicates(subset="ISBN", keep="first")
    result_df = exclude_ssu_data(result_df)

    needed_count = needed_input // len(kdc_list)

    # 각 KDC 범위에서 책 추천
    for kdc in kdc_list:
        if kdc % 100 == 0:
            filtered_df = result_df[result_df["KDC"] // 100 == kdc // 100]
        else:
            filtered_df = result_df[result_df["KDC"] // 10 == kdc // 10]

        sorted_filtered_df = filtered_df.head(needed_count)

        # 책 정보 추출
        for idx, ser in sorted_filtered_df.iterrows():
            book_info = {
                'ISBN'  : ser['ISBN'],
                '상품명'  :ser['서명'],
                '저자'   : ser['저자'],
                '출판사': ser['출판사'],
                '분야' : ser['상세 장르']
            }
            book_list.append(book_info)

    for idx, ser in result_df.iterrows():
        book_info = {
            'ISBN'  : ser['ISBN'],
            '상품명'  :ser['서명'],
            '저자'   : ser['저자'],
            '출판사': ser['출판사'],
            '분야' : ser['상세 장르']
        }
        book_list.append(book_info)
        if len(book_list) > needed_input:
            break
    result_df = pd.DataFrame(book_list)
    # ISBN별 개수를 "권수" 컬럼에 추가
    result_df["권수"] = result_df.groupby("ISBN")["ISBN"].transform("count")

    # 중복된 ISBN을 하나로 합치고, 첫 번째 책 정보만 남김
    result_df = result_df.drop_duplicates(subset=["ISBN"], keep="first")

    # 누적 권수를 계산하면서 needed_count권까지 선택
    result_df["누적권수"] = result_df["권수"].cumsum()
    result_df = result_df[result_df["누적권수"] <= needed_input]

    # 필요 없어진 "누적권수" 컬럼 삭제
    # result_df = result_df.drop(columns=["누적권수"])
    result_df.to_csv(f'{common.save_file_path}/genre_book_recommendations.csv', index=False, encoding='utf-8')  # UTF-8 인코딩으로 저장

# 실행
if __name__ == "__main__":
    main(8000)