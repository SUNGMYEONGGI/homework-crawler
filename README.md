# FastCampus LMS Crawler API v2.0

FastCampus LMS 시험 상세 페이지에서 학생 정보와 과제(블로그 링크 등)를 자동으로 수집하는 웹 기반 크롤러입니다. Selenium 기반 자동화, 실시간 WebSocket 로그, 다양한 파일 포맷 저장, 최신 UI/UX(다크테마, 글래스모피즘)까지 모두 지원합니다.

---

## ✨ 주요 기능
- 🤖 **자동 크롤링**: Selenium으로 자동 로그인 및 데이터 수집
- 📡 **실시간 진행상황**: WebSocket으로 실시간 로그/진행률 표시
- 📁 **다양한 파일 형식**: CSV, Excel(XLSX), JSON, XML 지원
- 🎨 **모던 UI/UX**: 다크 테마, 글래스모피즘, 반응형 디자인
- 🖱️ **원클릭 다운로드**: 결과 파일 즉시 다운로드

---

## 🚀 빠른 시작

### 1. 필요 조건
- Python 3.8 이상
- Chrome 브라우저(최신 버전)

### 2. 설치
```bash
pip install -r requirements.txt
```

### 3. 실행
```bash
python main.py
# 또는
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 접속
브라우저에서 [http://localhost:8000](http://localhost:8000) 접속

---

## 📋 사용법
1. **시험 ID 입력**: FastCampus LMS 시험 상세 페이지 URL의 숫자(ID)만 입력 (예: `https://lmsadmin-kdt.fastcampus.co.kr/exams/8532/detail` → `8532`)
2. **파일 형식 선택**: CSV, Excel(XLSX), JSON, XML 중 선택
3. **크롤링 시작**: "크롤링 시작" 버튼 클릭
4. **실시간 모니터링**: 진행률/로그/에러를 실시간 확인
5. **결과 다운로드**: 완료 후 "파일 다운로드" 버튼 클릭

---

## ��️ 기술 스택
### Backend
- **FastAPI**: 비동기 Python 웹 프레임워크
- **Selenium**: Chrome 자동화 (webdriver-manager로 자동 설치)
- **WebSocket**: 실시간 통신
- **Pandas**: 데이터 처리/파일 저장
- **openpyxl**: Excel 저장

### Frontend
- **Vanilla JS (ES6+)**: API 호출, WebSocket, UI 상태 관리
- **CSS3**: 다크테마, 글래스모피즘, 그라데이션, 반응형
- **Font Awesome**: 아이콘
- **Inter Font**: 모던 타이포그래피

---

## 📁 폴더 구조
```
fastcampus-crawler-api/
├── main.py            # FastAPI 서버/엔드포인트
├── crawler.py         # Selenium 크롤러 로직
├── requirements.txt   # 의존성 목록
├── README.md          # 프로젝트 설명서
└── static/            # 프론트엔드 리소스
    ├── index.html     # 메인 UI
    ├── style.css      # 스타일
    └── script.js      # 프론트엔드 JS
```

---

## 💻 Windows(윈도우) 환경 안내

윈도우 환경에서도 본 프로젝트를 문제없이 실행할 수 있습니다. 아래 내용을 참고하세요.

### 1. Python 및 Chrome 설치
- [Python 공식 사이트](https://www.python.org/downloads/windows/)에서 Python 3.8 이상 설치
- [Chrome 브라우저](https://www.google.com/chrome/) 최신 버전 설치
- 설치 후, python, pip, chrome이 모두 환경변수(PATH)에 등록되어 있는지 확인

### 2. 의존성 설치
```bash
# 명령 프롬프트(cmd) 또는 PowerShell에서 실행
pip install -r requirements.txt
```

### 3. 실행 방법
```bash
# 명령 프롬프트(cmd) 또는 PowerShell에서 실행
python main.py
# 또는
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. 크롬드라이버 관련 안내
- `webdriver-manager`가 자동으로 크롬드라이버를 설치하므로 별도 수동 설치 불필요
- 크롬 브라우저와 드라이버 버전이 맞지 않을 경우, 크롬을 최신으로 업데이트하거나 기존 드라이버를 삭제 후 재실행
- 방화벽/백신 프로그램이 크롬 또는 드라이버 실행을 차단하지 않도록 예외 처리 필요
- 일부 회사/학교 PC에서는 관리자 권한이 필요할 수 있음

### 5. 자주 발생하는 윈도우 환경 이슈
- **권한 문제**: "chromedriver.exe 실행 권한 없음" → 관리자 권한으로 실행
- **경로 문제**: 한글/공백이 포함된 경로에서 오류 발생 가능 → 영문 경로 사용 권장 (예: `C:\workspace\fastcampus-crawler-api`)
- **가상환경(venv) 사용**: 가상환경을 사용하는 경우, 반드시 해당 환경을 활성화 후 실행
- **윈도우 Defender/백신**: 드라이버 실행 차단 시 예외 등록

### 6. 기타
- 윈도우10/11 모두 정상 동작 확인됨
- 만약 "chrome이 설치되어 있지 않습니다" 또는 "드라이버를 찾을 수 없습니다" 에러 발생 시, 크롬 설치 경로를 환경변수에 추가하거나 크롬을 재설치
- 추가적인 윈도우 특화 에러가 발생하면 에러 메시지와 함께 이슈를 남겨주세요

---

## ⚠️ 계정 정보 하드코딩 안내

- `fastcampus-crawler-api/crawler.py` 파일의 20~21번째 줄에 **제로베이스 LMS 계정(이메일, 비밀번호)**를 직접 하드코딩해야 합니다.
    - 예시)
      ```python
      self.email = "your_lms_email@example.com"
      self.password = "your_lms_password"
      ```
- 실제 서비스/배포 환경에서는 보안상 환경변수 또는 별도 설정 파일로 관리하는 것이 안전합니다.
- 교육/개인 테스트 목적이 아니라면 절대 깃허브 등 공개 저장소에 계정 정보를 올리지 마세요!

---# homework-crawler
