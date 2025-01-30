import tkinter as tk
from tkinter import messagebox
import threading
from tkinter import ttk
import time
import queue

import genre_search as gs
import keyword_search as ks
import new_search as ns
import bestseller_search as bs
import engraft_books as eb
import common as common

class BookRecommendationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("도서 추천 시스템")
        
        # 검색 진행 여부 플래그
        self.searching = False
        self.queue = queue.Queue()
        
        # 필요한 도서 권 수 입력
        self.needed_book_count_label = tk.Label(root, text="필요한 도서 권 수 입력:")
        self.needed_book_count_label.pack(pady=5)

        self.needed_book_count_entry = tk.Entry(root, width=20)
        self.needed_book_count_entry.pack(pady=5)

        # '확인' 버튼
        self.search_button = tk.Button(root, text="확인", command=self.search_books)
        self.search_button.pack(pady=5)

        # 결과 출력 영역 + 스크롤바
        self.result_frame = tk.Frame(root)
        self.result_frame.pack(pady=5)
        
        self.scrollbar = tk.Scrollbar(self.result_frame)
        self.result_text = tk.Text(self.result_frame, width=60, height=20, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.result_text.yview)
        self.result_text.pack(side=tk.LEFT)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Progressbar 생성
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

    def update_result_text(self, message):
        """ 결과 텍스트를 안전하게 업데이트하는 함수 """
        self.queue.put(message)
        self.root.after(100, self.process_queue)

    def process_queue(self):
        """ 대기열에서 메시지를 가져와서 GUI에 업데이트 """
        while not self.queue.empty():
            message = self.queue.get()
            self.result_text.insert(tk.END, message + "\n")
            self.result_text.yview(tk.END)

    def update_progress_message(self, dot_count):
        """ 진행 메시지를 주기적으로 업데이트 (검색 종료 시 중단) """
        if not self.searching:
            return
        dots = '.' * (dot_count % 4)
        self.update_result_text(f"조회를 시작합니다{dots}")
        self.root.after(300, self.update_progress_message, dot_count + 1)

    def update_elapsed_time(self, start_time):
        """ 실시간으로 경과 시간을 업데이트하는 함수 """
        while self.searching:  # 검색이 진행 중일 때만 실행
            elapsed_time = time.time() - start_time
            elapsed_minutes = int(elapsed_time // 60)
            elapsed_seconds = int(elapsed_time % 60)

            # 이전 경과 시간 메시지 삭제 (마지막 줄만 유지)
            self.result_text.delete("end-2l", "end-1l")  # 마지막 두 줄 중 하나 삭제
            self.update_result_text(f"⏳ 경과 시간: {elapsed_minutes}분 {elapsed_seconds}초")

            time.sleep(1)  


    def search_books_in_background(self):
        """ 백그라운드에서 검색 실행 """
        start_time = time.time()
        needed_input = int(self.needed_book_count_entry.get().strip())

        self.update_result_text("검색을 시작합니다... 15분 소요 예상")
        self.progress['maximum'] = 100
        self.progress['value'] = 0
        self.searching = True

        common.create_result_folder()

        # 개수 분배
        genre_needed_count = round(needed_input * 0.4)
        keyword_needed_count = round(needed_input * 0.2)
        new_needed_count = round(needed_input * 0.2)
        bestseller_needed_count = needed_input - (genre_needed_count + keyword_needed_count + new_needed_count)

        # ✅ 실시간 경과 시간 업데이트 스레드 시작
        threading.Thread(target=self.update_elapsed_time, args=(start_time,), daemon=True).start()

        # 각 검색 실행
        gs.main(genre_needed_count)
        self.progress['value'] += 20

        ks.main(keyword_needed_count)
        self.progress['value'] += 20

        ns.main(new_needed_count)
        self.progress['value'] += 20

        bs.main(bestseller_needed_count)
        self.progress['value'] += 20

        eb.main(needed_input)
        self.progress['value'] += 20

        # 전체 소요 시간 계산
        elapsed_time = time.time() - start_time
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = int(elapsed_time % 60)

        self.update_result_text(f"\n✅ 전체 소요 시간: {elapsed_minutes}분 {elapsed_seconds}초")
        self.update_result_text(f"\n📂 저장 경로: {common.get_download_path()}/combined_book_recommendations.csv")

        self.searching = False  # 검색 종료
        self.progress['value'] = 100

    def validate_input(self):
        """ 입력값 검증 """
        try:
            needed_input = int(self.needed_book_count_entry.get().strip())
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

    def search_books(self):
        """ 검색 버튼 클릭 시 실행 """
        if self.validate_input():
            threading.Thread(target=self.search_books_in_background, daemon=True).start()
            self.update_progress_message(0)
            self.update_elapsed_time(time.time())

# GUI 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = BookRecommendationApp(root)
    root.mainloop()