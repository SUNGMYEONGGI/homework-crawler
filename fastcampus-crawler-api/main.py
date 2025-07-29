from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import asyncio
import json
import os
from crawler import FastCampusLMSCrawler
from typing import Optional
import time

app = FastAPI(title="FastCampus LMS Crawler API", version="2.0.0")

# 정적 파일 서빙 (HTML, CSS, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# 글로벌 크롤러 인스턴스
crawler_instance = None
websocket_connections = []

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
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # 연결이 끊어진 경우 제거
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

manager = ConnectionManager()

@app.get("/")
async def read_root():
    """메인 페이지 반환"""
    return FileResponse("static/index.html")

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 연결 관리"""
    await manager.connect(websocket)
    try:
        while True:
            # 클라이언트로부터 메시지 수신 (keep alive 등)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/crawl")
async def start_crawl(request: CrawlRequest, background_tasks: BackgroundTasks):
    """크롤링 시작"""
    global crawler_instance
    
    if not request.exam_id.isdigit():
        raise HTTPException(status_code=400, detail="올바른 시험 ID(숫자)를 입력하세요.")
    
    if crawler_instance and crawler_instance.is_running:
        raise HTTPException(status_code=409, detail="이미 다른 크롤링 작업이 실행 중입니다.")
    
    # 백그라운드에서 크롤링 실행
    background_tasks.add_task(run_crawling_task, request.exam_id, request.file_format)
    
    return {"message": "크롤링이 시작되었습니다.", "exam_id": request.exam_id}

@app.post("/api/stop")
async def stop_crawl():
    """크롤링 중지"""
    global crawler_instance
    
    if not crawler_instance or not crawler_instance.is_running:
        return {"message": "현재 실행 중인 크롤링 작업이 없습니다."}
    
    crawler_instance.cleanup()
    await manager.send_message(json.dumps({
        "type": "info",
        "message": "크롤링 중지 요청됨. 드라이버가 종료되었습니다."
    }))
    
    return {"message": "크롤링이 중지되었습니다."}

@app.get("/api/status")
async def get_status():
    """현재 크롤링 상태 조회"""
    global crawler_instance
    
    if not crawler_instance:
        return {"is_running": False, "current_exam_id": None}
    
    return {
        "is_running": crawler_instance.is_running,
        "current_exam_id": crawler_instance.current_exam_id
    }

@app.get("/api/download/{filename}")
async def download_file(filename: str):
    """결과 파일 다운로드"""
    file_path = filename
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

async def run_crawling_task(exam_id: str, file_format: str):
    """백그라운드에서 실행되는 크롤링 작업"""
    global crawler_instance
    
    try:
        crawler_instance = FastCampusLMSCrawler()
        
        # 로그 콜백 함수
        async def log_callback(message: str):
            await manager.send_message(json.dumps({
                "type": "log",
                "message": message
            }))
        
        # 진행률 콜백 함수
        async def progress_callback(progress: float, desc: str):
            await manager.send_message(json.dumps({
                "type": "progress",
                "progress": progress,
                "description": desc
            }))
        
        # 로그인 시작
        await log_callback("로그인 시도 중...")
        await progress_callback(0.1, "로그인 시도 중...")
        
        crawler_instance.login_process()
        
        await log_callback("로그인 성공. 데이터 수집 시작...")
        await progress_callback(0.2, "로그인 성공. 데이터 수집 시작...")
        
        # 크롤링 실행
        collected_count = await crawler_instance.crawl_exam_data_async(
            exam_id, progress_callback, log_callback
        )
        
        await progress_callback(0.9, f"{collected_count}개 데이터 수집 완료. 파일 생성 중...")
        
        if collected_count > 0:
            file_path = crawler_instance.export_data(exam_id, file_format)
            if file_path:
                await log_callback(f"크롤링 완료! 총 {collected_count}개의 데이터가 수집되어 '{file_path}' 파일에 저장되었습니다.")
                await manager.send_message(json.dumps({
                    "type": "complete",
                    "message": f"크롤링 완료! {collected_count}개 데이터 수집됨",
                    "file_path": file_path,
                    "count": collected_count
                }))
            else:
                await log_callback(f"데이터 수집은 완료되었으나 파일 생성에 실패했습니다 (형식: {file_format}).")
                await manager.send_message(json.dumps({
                    "type": "error",
                    "message": f"파일 생성 실패 (형식: {file_format})"
                }))
        else:
            await log_callback(f"데이터를 수집하지 못했습니다. (시험 ID: {exam_id})")
            await manager.send_message(json.dumps({
                "type": "error", 
                "message": f"데이터 수집 실패 (시험 ID: {exam_id})"
            }))
            
        await progress_callback(1.0, "작업 완료")
        
    except Exception as e:
        error_message = f"오류 발생: {str(e)}"
        await log_callback(error_message)
        await manager.send_message(json.dumps({
            "type": "error",
            "message": error_message
        }))
    finally:
        if crawler_instance:
            crawler_instance.cleanup()
        await log_callback("클린업 완료. 작업 종료.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 