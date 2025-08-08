# 📚 과제 리마인더 봇

FastCampus LMS에서 과제 제출 현황을 자동으로 확인하고, 미제출 학생들에게 슬랙으로 리마인더를 전송하는 웹 애플리케이션입니다.

## ✨ 주요 기능

- 🔍 **자동 크롤링**: FastCampus LMS에서 과제 제출 현황 자동 수집
- 📊 **시각적 대시보드**: 제출/미제출 현황을 한눈에 확인
- 💬 **슬랙 알림**: 미제출 학생들에게 자동으로 리마인더 전송
- 📱 **웹 인터페이스**: 브라우저에서 쉽게 사용 가능
- 📄 **데이터 내보내기**: CSV 형태로 결과 다운로드

## 🚀 설치 및 실행

### 1. 저장소 클론
```bash
git clone <repository-url>
cd homework-reminder-bot
```

### 2. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 또는
venv\Scripts\activate     # Windows
```

### 3. 필요한 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. ChromeDriver 설치 (macOS)
```bash
brew install chromedriver
```

### 5. 환경변수 설정
`.env` 파일을 생성하고 다음 내용을 입력:

```env
# 슬랙 봇 설정
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_CHANNEL=#homework-reminders

# FastCampus LMS 계정 (이미 코드에 하드코딩되어 있음)
FASTCAMPUS_EMAIL=help.edu@fastcampus.co.kr
FASTCAMPUS_PASSWORD=Camp1017!!
```

### 6. 애플리케이션 실행
```bash
python app.py
```

웹브라우저에서 표시된 URL로 접속합니다. (보통 `http://localhost:5000` 또는 `http://localhost:5001`)

## 🔧 슬랙 봇 설정

### 1. 슬랙 앱 생성
1. [Slack API](https://api.slack.com/apps)에 접속
2. "Create New App" → "From scratch" 선택
3. 앱 이름과 워크스페이스 선택

### 2. 봇 토큰 생성
1. "OAuth & Permissions" 메뉴로 이동
2. "Scopes" → "Bot Token Scopes"에서 다음 권한 추가:
   - `chat:write`
   - `chat:write.public`
   - `channels:read`
   - `groups:read`

3. "Install to Workspace" 클릭
4. 생성된 "Bot User OAuth Token" 복사 (`xoxb-`로 시작)

### 3. 채널 설정
1. 슬랙에서 리마인더를 보낼 채널 생성
2. 해당 채널에 봇 초대: `/invite @봇이름`

## 📖 사용 방법

### 1. 시험 ID 확인
FastCampus LMS에서 확인하고 싶은 시험의 URL에서 ID를 추출:
```
https://lmsadmin-kdt.fastcampus.co.kr/exams/12345/detail
                                           ^^^^^ 
                                         시험 ID
```

### 2. 웹 인터페이스 사용
1. 브라우저에서 앱 실행 후 표시된 URL 접속
2. 시험 ID 입력
3. "과제 현황 확인 시작" 버튼 클릭
4. 크롤링 완료 후 결과 확인
5. "슬랙으로 리마인더 전송" 버튼 클릭

### 3. 직접 실행 (테스트용)
```bash
python main.py
```

## 📁 프로젝트 구조

```
homework-reminder-bot/
├── app.py              # Flask 웹 애플리케이션
├── main.py             # 메인 크롤링 로직
├── slack_bot.py        # 슬랙 봇 기능
├── requirements.txt    # 필요한 패키지 목록
├── README.md          # 프로젝트 가이드
├── templates/         # HTML 템플릿
│   ├── base.html
│   ├── index.html
│   └── results.html
└── .env              # 환경변수 (직접 생성 필요)
```

## 🎯 수강생 리스트

현재 다음 학생들이 등록되어 있습니다:

```
고민서, 권문진, 권효주, 김동근, 김소은, 김수현, 김예인, 
김재록, 김종범, 김종화, 김진우, 김하은, 문서연, 박준수, 
박준영, 손은혜, 안현태, 오정택, 원정연, 유영호, 윤소영, 
이동건, 이수민, 이승호, 이재윤, 임환석, 정무곤, 정용재, 
주예령, 최보경, 최해혁, 최현, 허예경, 황은혜, 황준승
```

수강생 리스트를 수정하려면 `main.py`의 `self.all_students` 배열을 편집하세요.

## 🚀 배포 (선택사항)

### Heroku 배포
1. Heroku CLI 설치
2. 프로젝트 루트에서:
```bash
heroku create your-app-name
heroku config:set SLACK_BOT_TOKEN=your-token
heroku config:set SLACK_CHANNEL=#your-channel
git push heroku main
```

### Railway 배포
1. Railway 계정 생성
2. GitHub 저장소 연결
3. 환경변수 설정
4. 자동 배포

## ⚠️ 주의사항

- **보안**: 슬랙 토큰과 LMS 계정 정보를 안전하게 관리하세요
- **크롤링**: 과도한 요청으로 인한 IP 차단을 방지하기 위해 적절한 지연시간을 두고 있습니다
- **브라우저**: ChromeDriver가 설치되어 있어야 합니다
- **권한**: 슬랙 봇이 해당 채널에 메시지를 보낼 권한이 있는지 확인하세요

## 🐛 문제 해결

### 포트 5000 사용 중 오류
macOS에서 AirPlay Receiver가 포트 5000을 사용하는 경우:
1. **자동 해결**: 앱이 자동으로 포트 5001을 사용합니다
2. **수동 해결**: System Preferences > General > AirDrop & Handoff에서 AirPlay Receiver 비활성화

### ChromeDriver 오류
```bash
brew install chromedriver
```

### 슬랙 봇 토큰 오류
- 토큰이 `xoxb-`로 시작하는지 확인
- 봇이 채널에 초대되어 있는지 확인
- 필요한 권한이 부여되어 있는지 확인

### 크롤링 실패
- FastCampus LMS 로그인 정보 확인
- 시험 ID가 올바른지 확인
- 네트워크 연결 상태 확인

## 📞 문의

문제가 발생하거나 개선사항이 있으시면 이슈를 등록해주세요.

---

Made with ❤️ for FastCampus students