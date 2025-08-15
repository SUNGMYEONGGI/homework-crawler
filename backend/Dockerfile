# Railway용 경량 이미지
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Chromium + 필요한 라이브러리 설치 (Selenium 헤드리스 실행에 필요)
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    ca-certificates \
    libglib2.0-0 \
    libgtk-3-0 \
    libgbm1 \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY ./requirements.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY ./app /app/app

# Uvicorn 실행 (Render/플랫폼이 PORT를 주입)
ENV PORT=8000 \
    CHROME_BINARY=/usr/bin/chromium
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
