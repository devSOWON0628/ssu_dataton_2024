import os
from selenium import webdriver

# 운영 체제에 따라 다운로드 폴더 경로를 반환하는 함수
def get_download_path():
    if os.name == 'nt':  # Windows
        return os.path.join(os.environ['USERPROFILE'], 'Downloads')
    else:  # macOS, Linux
        return os.path.join(os.path.expanduser('~'), 'Downloads')
# WebDriver 옵션 설정
def get_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("lang=ko_KR")
    return options

# 파일 삭제 함수        
def file_delete(source):
    try:
        if os.path.exists(source):
            os.remove(source)
        
    except Exception as e:
        print(f"파일 이동 중 오류가 발생했습니다: {e}")
        
aladin_exclude_keywords     = {"초등", "유아", "영유아", "어린이", "중등", "만화"}
resource_file_path          = "resources"
save_file_path              = "result"
aladin_key                  = "ttbsowonpass1641001"
data4library_key            = "c85718a839ab138c1df4b4802bd6b72df0162743df65400ba97d6fa13875c1b0"