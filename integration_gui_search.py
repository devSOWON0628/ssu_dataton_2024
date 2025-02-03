import  tkinter as tk
from    tkinter import messagebox
from    tkinter import ttk
import  threading
import  time
import  queue

import genre_search         as gs       # 선호 장르 기반 추천
import keyword_search       as ks       # 키워드 기반 추천
import new_search           as ns       # 신간 기반 추천
import bestseller_search    as bs       # 베스트셀러 기반 추천
import engraft_books        as eb       # 엑셀 병합 및 최종 추천
import common               as common   # 공통 함수

class BookRecommendationApp:
    
    # 도서 추천 시스템 GUI 초기화
    # - 필요한 도서 권 수 입력 필드 생성
    # - 검색 버튼 생성
    # - 결과 출력 영역 및 진행 상태 표시 UI 구성
    def __init__(self, root):
        self.root = root
        self.root.title("도서 추천 시스템")
        
        self.searching = False      # 검색 진행 여부 플래그
        self.queue = queue.Queue()  # GUI 업데이트를 위한 메시지 큐
        
        # 필요한 도서 권 수 입력 필드
        self.needed_book_count_label = tk.Label(root, text="필요한 도서 권 수 입력:")
        self.needed_book_count_label.pack(pady=5)

        self.needed_book_count_entry = tk.Entry(root, width=20)
        self.needed_book_count_entry.pack(pady=5)

        # 검색 시작 버튼
        self.search_button = tk.Button(root, text="확인", command=self.search_books)
        self.search_button.pack(pady=5)

        # 결과 출력 영역
        self.result_frame = tk.Frame(root)
        self.result_frame.pack(pady=5)
        
        self.scrollbar = tk.Scrollbar(self.result_frame)
        self.result_text = tk.Text(self.result_frame, width=60, height=20, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.result_text.yview)
        self.result_text.pack(side=tk.LEFT)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 진행 상태 표시 (Progressbar)
        self.progress = ttk.Progressbar(root, orient="horizontal", length=300, mode="determinate")
        self.progress.pack(pady=10)

    # 결과 텍스트를 안전하게 업데이트하는 함수 (GUI 스레드에서 실행)
    def update_result_text(self, message):
        self.queue.put(message)
        self.root.after(100, self.process_queue)

    # 대기열에서 메시지를 가져와 결과 창에 출력
    def process_queue(self):
        
        while not self.queue.empty():
            message = self.queue.get()
            self.result_text.insert(tk.END, message + "\n")
            self.result_text.yview(tk.END)

    # 진행 메시지를 주기적으로 업데이트하여 사용자에게 진행 상황을 알림
    def update_progress_message(self, dot_count):
        if not self.searching:
            return
        dots = '.' * (dot_count % 4)
        self.update_result_text(f"조회를 시작합니다{dots}")
        self.root.after(300, self.update_progress_message, dot_count + 1)

    # 검색 실행 중 실시간 경과 시간을 업데이트
    def update_elapsed_time(self, start_time):
        while self.searching:
            elapsed_time = time.time() - start_time
            elapsed_minutes = int(elapsed_time // 60)
            elapsed_seconds = int(elapsed_time % 60)
            
            self.result_text.delete("end-2l", "end-1l")  # 마지막 두 줄 중 하나 삭제
            self.update_result_text(f"⏳ 경과 시간: {elapsed_minutes}분 {elapsed_seconds}초")
            
            time.sleep(1)  # 1초 간격으로 업데이트


    # 도서 추천을 백그라운드에서 실행 (멀티스레딩)
    def search_books_in_background(self):
        start_time = time.time()
        needed_input = int(self.needed_book_count_entry.get().strip())
        
        self.update_result_text("검색을 시작합니다... 15분 소요 예상")
        self.progress['maximum'] = 100
        self.progress['value'] = 0
        self.searching = True  # 검색 시작 플래그 설정
        
        common.create_result_folder()  # 결과 저장 폴더 생성
        
        # 도서 개수 비율에 따라 검색할 권 수 계산
        genre_needed_count      = round(needed_input * 0.4)
        keyword_needed_count    = round(needed_input * 0.2)
        new_needed_count        = round(needed_input * 0.2)
        bestseller_needed_count = needed_input - (genre_needed_count + keyword_needed_count + new_needed_count)

        # 실시간 경과 시간 업데이트 스레드 실행
        threading.Thread(target=self.update_elapsed_time, args=(start_time,), daemon=True).start()

        # 개별 검색 실행
        gs.main(genre_needed_count)
        self.progress['value'] += 20

        ks.main(keyword_needed_count)
        self.progress['value'] += 20

        ns.main(new_needed_count)
        self.progress['value'] += 20

        bs.main(bestseller_needed_count)
        self.progress['value'] += 20

        eb.main(needed_input)  # 최종 결과 병합
        self.progress['value'] += 20

        # 총 소요 시간 출력
        elapsed_time = time.time() - start_time
        elapsed_minutes = int(elapsed_time // 60)
        elapsed_seconds = int(elapsed_time % 60)
        self.update_result_text(f"\n✅ 전체 소요 시간: {elapsed_minutes}분 {elapsed_seconds}초")
        self.update_result_text(f"\n📂 저장 경로: {common.get_download_path()}/combined_book_recommendations.csv")
        
        self.searching = False  # 검색 종료
        self.progress['value'] = 100

    # 사용자 입력값 validation (숫자 입력 및 범위 체크)
    def validate_input(self):
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

    # 검색 버튼 클릭 시 실행
    def search_books(self):
        if self.validate_input():
            threading.Thread(target=self.search_books_in_background, daemon=True).start()
            self.update_progress_message(0)
            self.update_elapsed_time(time.time())

# GUI 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = BookRecommendationApp(root)
    root.mainloop()