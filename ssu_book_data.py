import pandas as pd
import common as common

def add_book_count_and_save(input_csv: str, output_csv: str):
    # CSV 파일 읽기
    df = pd.read_csv(input_csv)
    
    # ISBN 기준으로 권수 계산
    book_counts = df['ISBN'].value_counts().reset_index()
    book_counts.columns = ['ISBN', '권수']
    
    # 원본 데이터에 권수 컬럼 추가
    df = df.merge(book_counts, on='ISBN', how='left')
    
    # 중복된 ISBN 제거하고 첫 번째 행만 유지
    df = df.drop_duplicates(subset=['ISBN'], keep='first')
    
    # CSV 파일로 저장
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"CSV 파일이 저장되었습니다: {output_csv}")

# 사용 예시
input_file = f"{common.resource_file_path}/book_data.csv"  # 입력 파일명
output_file = f"{common.resource_file_path}/books_with_count.csv"  # 출력 파일명
add_book_count_and_save(input_file, output_file)