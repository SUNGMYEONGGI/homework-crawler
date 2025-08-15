## Homework Crawler

Fastcampus LMS 과제(블로그 링크 등)를 자동 수집·정리하는 대시보드/크롤러

### 한 줄 설명
- 프론트(Next.js)에서 시험 ID와 결과 파일 형식을 입력 → 백엔드(FastAPI)가 비동기로 크롤링 → 진행률/로그를 실시간(WebSocket)으로 보여주고, CSV/XLSX/JSON/XML 파일로 다운로드합니다.

---

## 프로젝트 개요

### 목적
- 운영자가 LMS 관리자 화면을 일일이 확인하지 않고, 과제 제출 내용을 자동으로 수집/정리하여 데이터 처리 시간을 단축합니다.

### 문제/해결
- 문제: 수강생 과제 URL/내용을 수동으로 집계하면 시간이 오래 걸리고, 누락/오류 가능성이 큼
- 해결: Selenium 기반 크롤링으로 제출 내역을 순회 수집, 실시간 진행률과 로그를 제공하여 투명성/안정성 확보. 한 번에 다양한 포맷으로 내보내 결과 공유가 쉬움

### 주요 기능
- 시험 ID 기준 과제 제출 데이터 수집
- 실시간 로그/진행률(WebSocket) 스트리밍
- 파일 저장 형식: CSV / XLSX / JSON / XML
- 일시 중지/중단, 상태 조회, 결과 파일 다운로드
- 환경변수 기반 보안(계정/도메인), CORS 제어
- 컨테이너 환경(Chromium)에서 안정적 헤드리스 실행

### 기대 효과/목표
- 운영자의 수작업을 자동화하여 처리 시간 절감
- 데이터 누락/편차 최소화, 결과의 일관성 확보
- 배포 자동화(Vercel/Render)로 유지보수 용이

---

## 폴더 구조

```
homework-crawler-main/
├─ backend/        # FastAPI + Selenium (Render 배포)
│  ├─ app/
│  │  ├─ main.py      # API, WebSocket(progress/log)
│  │  └─ crawler.py   # Selenium 크롤러
│  ├─ requirements.txt
│  └─ Dockerfile
└─ frontend/       # Next.js + TS + Tailwind + shadcn (Vercel 배포)
   ├─ app/
   │  ├─ page.tsx      # 메인 화면(수집 설정/진행률/로그/다운로드)
   │  ├─ layout.tsx
   │  └─ globals.css   # 컬러 토큰(Fastcampus 톤)
   ├─ components/
   │  └─ ui/           # shadcn 컴포넌트(overlay 등 포함)
   └─ tailwind.config.ts 외 설정 파일들
```

---

## 기술 스택

<p>
  <img alt="Next.js" src="https://img.shields.io/badge/Next.js-000?style=for-the-badge&logo=next.js&logoColor=white" />
  <img alt="TypeScript" src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" />
  <img alt="TailwindCSS" src="https://img.shields.io/badge/TailwindCSS-38B2AC?style=for-the-badge&logo=tailwindcss&logoColor=white" />
  <img alt="shadcn/ui" src="https://img.shields.io/badge/shadcn%2Fui-111?style=for-the-badge&logo=radixui&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" />
  <img alt="Python" src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img alt="Selenium" src="https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white" />
  <img alt="Docker" src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" />
  <img alt="Vercel" src="https://img.shields.io/badge/Vercel-000?style=for-the-badge&logo=vercel&logoColor=white" />
  <img alt="Render" src="https://img.shields.io/badge/Render-46E3B7?style=for-the-badge&logo=render&logoColor=111827" />
</p>

---

## 빠른 시작 (로컬)

### 요구사항
- Python 3.11+
- Node.js 18+ / npm
- Chrome/Chromium 설치(로컬 실행 시)

### 1) 백엔드 실행
1. `.env` 작성 (예: `backend/.env`)
```
FASTCAMPUS_EMAIL=your_id@example.com
FASTCAMPUS_PASSWORD=your_password
CORS_ORIGINS=http://localhost:3000
CHROME_HEADLESS=true
# 필요 시 바이너리 경로 지정 (Mac 예시)
# CHROME_BINARY=/Applications/Google Chrome.app/Contents/MacOS/Google Chrome
PORT=8000
```
2. 패키지 설치 및 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 2) 프론트엔드 실행
1. `frontend/.env.local` 작성
```
NEXT_PUBLIC_API_BASE=http://localhost:8000
```
2. 설치 및 실행
```bash
cd frontend
npm i
npm run dev
```
3. 브라우저에서 `http://localhost:3000` 접속 → 시험 ID/형식 선택 → 수집 시작

---

## 환경변수

### 백엔드 (Render)
- `FASTCAMPUS_EMAIL` / `FASTCAMPUS_PASSWORD`: LMS 로그인 계정
- `CORS_ORIGINS`: 허용할 프론트엔드 Origin(콤마 구분). 예) `https://your-app.vercel.app`
- `CHROME_HEADLESS`(기본 true): 헤드리스 실행 토글
- `CHROME_BINARY`(선택): chromium/chrome 바이너리 경로 (컨테이너/서버 환경에서 권장)
- `PORT`: 플랫폼이 주입 (Dockerfile은 `${PORT}` 사용)

### 프론트엔드 (Vercel)
- `NEXT_PUBLIC_API_BASE`: 백엔드 베이스 URL
  - Production: `https://<render-service>.onrender.com`
  - Preview: 같은 값 또는 스테이징 URL (권장)
  - Development: 로컬 개발 시 `.env.local`로 `http://localhost:8000`

---

## 배포

### 백엔드(Render)
1. New → Web Service → GitHub 연결, Root Directory: `backend`
2. Runtime: Docker 자동 감지 (이미지에 chromium/chromedriver 설치)
3. Env: `FASTCAMPUS_EMAIL`, `FASTCAMPUS_PASSWORD`, `CORS_ORIGINS`, 필요 시 `CHROME_BINARY=/usr/bin/chromium`
4. Health Check: `/api/health`
5. 배포 후 제공 URL 복사 → 프론트의 `NEXT_PUBLIC_API_BASE`로 설정

### 프론트엔드(Vercel)
1. New Project → GitHub Import, Root Directory: `frontend`
2. Env: `NEXT_PUBLIC_API_BASE`를 Render URL로 설정 (Production/Preview/Development)
3. 빌드/배포 → `https://<your-vercel>.vercel.app`

---

## API 개요
- `GET /api/health` → 상태 확인
- `POST /api/crawl` → 바디 `{ exam_id: string, file_format: "csv|xlsx|json|xml" }`
- `POST /api/stop` → 진행 중인 크롤링 중지
- `GET /api/status` → 현재 상태
- `GET /api/download/{filename}` → 결과 다운로드
- `WS /ws` (텍스트 메시지)
  - `{ type: "log", message: string }`
  - `{ type: "progress", progress: number(0~1), description: string }`
  - `{ type: "complete", file_path: string, count: number }`
  - `{ type: "error", message: string, details?: string }`

---

## 문제 해결(Troubleshooting)

### 1) 프런트에서 `OPTIONS /api/crawl 400` (프리플라이트 실패)
- Render `CORS_ORIGINS`에 Vercel 도메인 추가(프로토콜 포함, 슬래시 없이). 예) `https://your-app.vercel.app`
- 여러 프리뷰 도메인 사용 시 콤마로 추가
- 값 변경 후 백엔드 재배포 필요

### 2) 크롤링 시작 시 브라우저 드라이버 에러
- 컨테이너/서버: `CHROME_BINARY` 지정권장(`/usr/bin/chromium`) + Dockerfile의 chromium 패키지 설치
- 로컬: 크롬/크롬드라이버 설치 확인

### 3) 로그가 안 찍힌다
- CORS 또는 `NEXT_PUBLIC_API_BASE` 오기재로 본 요청이 백엔드에 도달하지 않은 경우가 대부분
- 네트워크 탭에서 요청 URL이 Render URL인지 확인

---

## 디자인/UX
- shadcn-ui 컴포넌트(Card, Button, Select, Progress 등) 기반
- Fastcampus 톤(마젠타) 컬러 토큰 적용: `frontend/app/globals.css`
- 연결 지연 시 "연결중" 오버레이: `frontend/components/ui/overlay-loading.tsx` (첫 로그 수신 시 자동 종료)

---

## 설치 및 실행 방법(자세)

1) 레포 클론 후 환경 변수 세팅
```bash
git clone https://github.com/SUNGMYEONGGI/homework-crawler.git
cd homework-crawler
# backend/.env, frontend/.env.local 작성 (아래 예시 참고)
```

2) 백엔드 실행
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

3) 프론트 실행
```bash
cd frontend
npm i
npm run dev
```

4) 접속 및 테스트
- 브라우저에서 `http://localhost:3000` → 시험 ID 입력 → 수집 시작 → 로그/진행률 확인 → 파일 다운로드

> 스크린샷/데모: 운영 중 배포 URL `https://homework-crawler.vercel.app/` 참고.

---

## 사용 방법

### 기본 플로우
1. 상단 "수집 설정" 카드에서 시험 ID 입력, 파일 형식 선택(CSV/XLSX/JSON/XML)
2. "수집 시작" 클릭 → 상단 히어로 보더 아래 진행률 바 + 실시간 로그 확인
3. 완료 시 우측 "다운로드" 카드에서 결과 파일 다운로드
4. 필요 시 "중지"로 현재 작업을 종료

### 기능별 사용 예시
- 실시간 로그: WebSocket으로 서버 로그가 도착하면 화면에 즉시 반영, 첫 로그가 도착하면 "연결중" 팝업은 자동으로 닫힘
- 중지: 크롤러 리소스 정리 후 상태 초기화(서버가 드라이버 quit)
- 파일 형식: 운영팀 공유 상황에 맞춰 CSV(범용) 혹은 XLSX(엑셀) 권장

---

## 라이선스
사내/과제용 예제로 별도 명시가 없는 한 내부 사용을 가정합니다.


