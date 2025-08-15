## Homework Crawler (Monorepo)

Fastcampus LMS 과제(블로그 링크 등)를 수집하는 크롤러입니다. 프론트엔드는 Next.js(Typescript, Tailwind, shadcn-ui), 백엔드는 FastAPI + Selenium으로 구성되어 있으며 각각 Vercel/Render에 배포합니다.

### 폴더 구조

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
- 연결 지연 시 "연결중" 오버레이: `frontend/components/ui/overlay-loading.tsx`

---

## 라이선스
사내/과제용 예제로 별도 명시가 없는 한 내부 사용을 가정합니다.


