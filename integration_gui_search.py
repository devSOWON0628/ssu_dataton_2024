import tkinter as tk
from tkinter import messagebox
import threading
from tkinter import ttk
import time  # 시간 측정을 위한 모듈

import genre_search as gs
import keyword_search as ks
import new_search as ns
import bestseller_search as bs
import engraft_books as eb
import common as common

# 장르 검색
def genre_search(genre_needed_count):
    if genre_needed_count <= 0:
        return
    gs.main(genre_needed_count)
    print(f"장르 검색이 저장되었습니다.")  # 저장 완료 메시지 출력
    
# 키워드 검색
def keyword_search(keyword_needed_count):
    if keyword_needed_count <= 0:
        return
    ks.main(keyword_needed_count)
    print(f"키워드 검색이 저장되었습니다.")
        
# 신간 검색
def new_search(new_needed_count):
    if new_needed_count <= 0:
        return
    ns.main(new_needed_count)
    print(f"신간 검색이 저장되었습니다.")
 
# 베스트셀러 검색   
def bestseller_search(bestseller_needed_count):
    if bestseller_needed_count <= 0:
        return
    bs.main(bestseller_needed_count)
    print(f"베스트셀러 검색이 저장되었습니다.")

def engraft(needed_input):
    eb.main(needed_input)
    print("합본이 저장되었습니다.")

# 진행 중 메시지 업데이트 함수
def update_progress_message(dot_count):
    # '.'을 최대 3개까지 갱신
    dots = '.' * (dot_count % 4)  # 3개까지만 반복
    result_text.delete(1.0, tk.END)
    result_text.insert(tk.END, f"조회를 시작합니다{dots}\n")
    result_text.insert(tk.END, "최대 10분이 소요됩니다.\n")
    # 1초 후에 다시 업데이트
    root.after(1000, update_progress_message, dot_count + 1)

# 백그라운드 검색 실행
def search_books_in_background():
    start_time = time.time()  # 시작 시간 기록
    
    needed_input = int(needed_book_count_entry.get().strip())
    result_text.delete(1.0, tk.END)
    
    # 진행 중 메시지 초기화
    update_progress_message(0)
    
    progress['maximum'] = 100  # Progressbar의 최대값 설정
    progress['value'] = 0  # 초기값 설정
    
    # 장르 검색
    genre_needed_count = int(needed_input * 0.4)
    print("장르검색", genre_needed_count)
    genre_search(genre_needed_count)
    progress['value'] += 20  # Progressbar 업데이트 (20%)
    
    # 키워드 검색
    keyword_needed_count = int(needed_input * 0.2)
    print("키워드검색", keyword_needed_count)
    keyword_search(keyword_needed_count)
    progress['value'] += 20  # Progressbar 업데이트 (20%)
    
    # 신간 검색
    new_needed_count = int(needed_input * 0.2)
    print("신간검색", new_needed_count)
    new_search(new_needed_count)
    progress['value'] += 20  # Progressbar 업데이트 (20%)
    
    # 베스트셀러 검색
    bestseller_needed_count = int(needed_input * 0.2)
    print("베스트셀러 검색", bestseller_needed_count)
    bestseller_search(bestseller_needed_count)
    progress['value'] += 20  # Progressbar 업데이트 (20%)
    
    # 합본
    engraft(needed_input)
    progress['value'] += 20  # Progressbar 업데이트 (20%)
    
    # 전체 소요 시간 계산
    end_time = time.time()  # 끝 시간 기록
    elapsed_time = end_time - start_time  # 시간 차이 계산
    elapsed_minutes = elapsed_time // 60  # 분 단위로 변환
    elapsed_seconds = int(elapsed_time % 60)  # 초 단위로 변환
    
    result_text.insert(tk.END, f"\n전체 소요 시간: {int(elapsed_minutes)}분 {elapsed_seconds}초\n")
    result_text.insert(tk.END, f"\n{common.save_file_path}/combined_book_recommendations.csv 경로에 파일이 저장되었습니다.")

# 입력값 검증 함수
def validate_input():
    try:
        needed_input = int(needed_book_count_entry.get().strip())
        if needed_input <= 0:
            messagebox.showerror("입력 오류", "도서 권수는 1권 이상이어야 합니다.")
            return False
        elif needed_input > 20000:
            messagebox.showerror("입력 오류", "도서 권수는 최대 20,000권까지 입력 가능합니다.")
            return False
        return True
    except ValueError:
        messagebox.showerror("입력 오류", "숫자만 입력 가능합니다.")
        return False

# 검색 버튼 실행 함수
def search_books():
    if validate_input():
        threading.Thread(target=search_books_in_background, daemon=True).start()

    # GUI 설정
root = tk.Tk()
root.title("도서 추천 시스템")

# 필요한 도서 권 수 입력
needed_book_count_label = tk.Label(root, text="필요한 도서 권 수 입력:")
needed_book_count_label.pack(pady=5)

needed_book_count_entry = tk.Entry(root, width=20)
needed_book_count_entry.pack(pady=5)

# '확인' 버튼
search_button = tk.Button(root, text="확인", command=search_books)
search_button.pack(pady=5)

# 결과 출력 영역
result_text = tk.Text(root, width=60, height=20)
result_text.pack(pady=5)

# Progressbar 생성 (mode="determinate"로 설정)
progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
progress.pack(pady=10)

# 실행
root.mainloop()
