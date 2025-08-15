from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
import os
from typing import Optional
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ python-dotenv로 환경변수 로드됨")
except Exception:
    print("⚠️ python-dotenv가 설치되지 않았거나 로드 실패. 시스템 환경변수만 사용됩니다.")

from .crawler import FastCampusLMSCrawler


app = FastAPI(title="FastCampus LMS Crawler API", version="2.0.0")

# CORS 설정 (Vercel 배포 도메인을 환경변수로 주입: CORS_ORIGINS= https://your-frontend.vercel.app,https://...)
raw_origins = os.getenv("CORS_ORIGINS", "*")
allowed_origins = [o.strip() for o in raw_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CrawlRequest(BaseModel):
    exam_id: str
    file_format: str = "csv"


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_message(self, message: str):
        for connection in list(self.active_connections):
            try:
                await connection.send_text(message)
            except Exception:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)


manager = ConnectionManager()

# 정적 파일은 프론트에서 처리하므로 서버에서는 제공하지 않음

crawler_instance: Optional[FastCampusLMSCrawler] = None


@app.get("/api/health")
async def health_check():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/crawl")
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    global crawler_instance

    if not request.exam_id.isdigit():
        raise HTTPException(status_code=400, detail="올바른 시험 ID(숫자)를 입력하세요.")

    if crawler_instance and crawler_instance.is_running:
        raise HTTPException(status_code=409, detail="이미 다른 크롤링 작업이 실행 중입니다.")

    background_tasks.add_task(run_crawling_task, request.exam_id, request.file_format)
    return {"message": "크롤링이 시작되었습니다.", "exam_id": request.exam_id}


@app.post("/api/stop")
async def stop_crawl():
    global crawler_instance

    if not crawler_instance or not crawler_instance.is_running:
        return {"message": "현재 실행 중인 크롤링 작업이 없습니다."}

    crawler_instance.cleanup()
    await manager.send_message(
        json.dumps({"type": "info", "message": "크롤링 중지 요청됨. 드라이버가 종료되었습니다."})
    )
    return {"message": "크롤링이 중지되었습니다."}


@app.get("/api/status")
async def get_status():
    global crawler_instance
    if not crawler_instance:
        return {"is_running": False, "current_exam_id": None}
    return {"is_running": crawler_instance.is_running, "current_exam_id": crawler_instance.current_exam_id}


@app.get("/api/download/{filename}")
async def download_file(filename: str):
    file_path = filename
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")


async def run_crawling_task(exam_id: str, file_format: str):
    global crawler_instance
    try:
        crawler_instance = FastCampusLMSCrawler()

        async def log_callback(message: str):
            await manager.send_message(json.dumps({"type": "log", "message": message}))

        async def progress_callback(progress: float, desc: str):
            await manager.send_message(
                json.dumps({"type": "progress", "progress": progress, "description": desc})
            )

        await log_callback("로그인 시도 중...")
        await progress_callback(0.1, "로그인 시도 중...")

        crawler_instance.login_process()

        await log_callback("로그인 성공. 데이터 수집 시작...")
        await progress_callback(0.2, "로그인 성공. 데이터 수집 시작...")

        collected_count = await crawler_instance.crawl_exam_data_async(exam_id, progress_callback, log_callback)

        await progress_callback(0.9, f"{collected_count}개 데이터 수집 완료. 파일 생성 중...")

        if collected_count > 0:
            file_path = crawler_instance.export_data(exam_id, file_format)
            if file_path:
                await log_callback(
                    f"크롤링 완료! 총 {collected_count}개의 데이터가 수집되어 '{file_path}' 파일에 저장되었습니다."
                )
                await manager.send_message(
                    json.dumps(
                        {
                            "type": "complete",
                            "message": f"크롤링 완료! {collected_count}개 데이터 수집됨",
                            "file_path": file_path,
                            "count": collected_count,
                        }
                    )
                )
            else:
                await log_callback(f"데이터 수집은 완료되었으나 파일 생성에 실패했습니다 (형식: {file_format}).")
                await manager.send_message(
                    json.dumps({"type": "error", "message": f"파일 생성 실패 (형식: {file_format})"})
                )
        else:
            await log_callback(f"데이터를 수집하지 못했습니다. (시험 ID: {exam_id})")
            await manager.send_message(
                json.dumps({"type": "error", "message": f"데이터 수집 실패 (시험 ID: {exam_id})"})
            )

        await progress_callback(1.0, "작업 완료")
    except Exception as e:
        import traceback

        error_str = str(e) if str(e) else f"타입: {type(e).__name__}"
        error_message = f"오류 발생: {error_str}"
        detailed_error = f"{error_message}\n상세 정보: {repr(e)}\n스택 트레이스:\n{traceback.format_exc()}"
        await manager.send_message(
            json.dumps({"type": "error", "message": error_message, "details": detailed_error})
        )
    finally:
        if crawler_instance:
            crawler_instance.cleanup()
        await manager.send_message(json.dumps({"type": "log", "message": "클린업 완료. 작업 종료."}))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))


