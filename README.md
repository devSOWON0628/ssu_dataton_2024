# 숭실대학교 2024 데이터톤
### 미래에 필요한 도서 추천 시스템

이 프로젝트는 숭실대학교의 미래 도서 필요에 맞는 도서를 추천하는 시스템입니다. 사용자가 입력한 도서 권수에 맞춰 네 가지 기준에 따라 도서를 추천하고, 결과를 CSV 파일 형식으로 저장합니다. 도서 추천은 다음과 같은 기준을 따릅니다:

1. 도서 추천 기준

 | 조건 | 비율 | 2만권 기준 |  |
| --- | --- | --- | --- |
| 숭실대학교 중앙도서관 선호 장르 기반 추천 | 40% | 8,000 | 정보나루 데이터 |
| 지난 달 인기 키워드 기반 추천 | 10% | 2,000 | 정보나루 |
| 최근 6개월간 신간 기반 추천 | 30% | 6,000 | [yes24](https://www.yes24.com/Product/Category/AttentionNewProduct?categoryNumber=001001&pageNumber=17&pageSize=120&newProductType=ATTENTION), [교보](https://product.kyobobook.co.kr/new/KOR#?page=1&sort=new&year=2024&month=11&week=4&per=20&saleCmdtDvsnCode=KOR&gubun=newGubun&saleCmdtClstCode=) 크롤링  |
| 최근 3년간 베스트셀러 기반 추천 | 20% | 4,000 | [yes24](https://www.yes24.com/Product/Category/BestSeller?categoryNumber=001&pageNumber=1&pageSize=200&goodsStatGb=06), [교보](https://store.kyobobook.co.kr/bestseller/total/weekly) 크롤링 |
2. 사용 방법

- 입력값:
필요한 도서 권수 (needed_book_count): 추천할 총 도서 권수를 입력합니다. 예: 2000권.
- 출력값:
추천된 도서 정보와 권수를 포함하는 CSV 파일을 반환합니다.
- 수행 과정:
    1. 도서 추천:
        - 각 기준에 따라 도서 권수를 추천합니다.
        - 숭실대학교 중앙도서관 선호 장르, 지난 달 인기 키워드, 최근 6개월 신간, 최근 3년 베스트셀러에 따라 도서 목록을 크롤링하고 권수를 계산합니다.
    2. 결과 병합:
각 기준에 맞게 수집된 도서 데이터를 병합합니다.
    3. 중복 도서 처리:
ISBN 기준으로 중복된 도서를 제거합니다.
    4. 권수 수정:
권수가 10권 이상인 도서는 10권으로 수정합니다.
    5. 추천 도서 권수 맞추기:
권수가 부족하면 부족한 만큼 추가 도서를 추천하여 채웁니다.
    6. CSV 파일로 저장:
최종적으로 추천된 도서 정보를 CSV 파일로 저장하여 반환합니다.