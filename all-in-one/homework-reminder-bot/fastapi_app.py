from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import asyncio
import json
import os
from main import HomeworkReminderBot
from slack_bolt_bot import SlackBoltReminderBot
from typing import Optional
import time

app = FastAPI(title="Homework Reminder Bot API", version="2.0.0")

# 정적 파일 서빙 (HTML, CSS, JS)
templates = Jinja2Templates(directory="templates")

# 글로벌 봇 인스턴스
bot_instance = None
websocket_connections = []
crawl_results = {}

class CrawlRequest(BaseModel):
    cohort_13: Optional[str] = ""
    cohort_14: Optional[str] = ""
    cohort_15: Optional[str] = ""
    cohort_16: Optional[str] = ""

class SlackRequest(BaseModel):
    cohort_exam_ids: dict
    non_submitted_by_cohort: dict
    channel: Optional[str] = None

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

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """메인 페이지 반환"""
    return FileResponse("templates/index_fastapi.html")

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

@app.post("/api/check_homework")
async def start_homework_check(request: CrawlRequest, background_tasks: BackgroundTasks):
    """과제 확인 시작"""
    global bot_instance
    
    # 기수별 시험 ID 수집
    cohort_exam_ids = {
        '13': request.cohort_13.strip() if request.cohort_13 else "",
        '14': request.cohort_14.strip() if request.cohort_14 else "",
        '15': request.cohort_15.strip() if request.cohort_15 else "",
        '16': request.cohort_16.strip() if request.cohort_16 else ""
    }
    
    # 최소 하나의 시험 ID가 있는지 확인
    valid_exams = [exam_id for exam_id in cohort_exam_ids.values() if exam_id]
    if not valid_exams:
        raise HTTPException(status_code=400, detail="최소 하나의 기수에 대한 시험 ID를 입력해주세요.")
    
    if bot_instance and hasattr(bot_instance, 'driver') and bot_instance.driver:
        raise HTTPException(status_code=409, detail="이미 다른 크롤링 작업이 실행 중입니다.")
    
    # 백그라운드에서 크롤링 실행
    background_tasks.add_task(run_homework_check_task, cohort_exam_ids)
    
    return {"message": "과제 확인을 시작했습니다.", "cohort_exam_ids": cohort_exam_ids}

@app.post("/api/stop")
async def stop_crawl():
    """크롤링 중지"""
    global bot_instance
    
    if not bot_instance or not hasattr(bot_instance, 'driver') or not bot_instance.driver:
        return {"message": "현재 실행 중인 크롤링 작업이 없습니다."}
    
    bot_instance.cleanup()
    await manager.send_message(json.dumps({
        "type": "info",
        "message": "크롤링 중지 요청됨. 드라이버가 종료되었습니다."
    }))
    
    return {"message": "크롤링이 중지되었습니다."}

@app.get("/api/status")
async def get_status():
    """현재 크롤링 상태 조회"""
    global bot_instance
    
    is_running = bot_instance and hasattr(bot_instance, 'driver') and bot_instance.driver is not None
    
    return {
        "is_running": is_running,
        "current_exam_id": getattr(bot_instance, 'current_exam_id', None) if bot_instance else None
    }

@app.get("/api/results")
async def get_results():
    """크롤링 결과 조회"""
    return crawl_results

@app.get("/api/logs")
async def get_logs():
    """실시간 로그 확인"""
    global bot_instance
    logs = []
    if bot_instance and hasattr(bot_instance, 'log_messages'):
        logs = bot_instance.log_messages[-20:]  # 최근 20개 로그만
    return {"logs": logs}

@app.post("/api/send_slack_reminder")
async def send_slack_reminder(request: SlackRequest):
    """슬랙 리마인더 전송"""
    try:
        # 전체 미제출 학생 수 계산
        total_non_submitted = sum(len(students) for students in request.non_submitted_by_cohort.values())
        
        if total_non_submitted == 0:
            return {"message": "미제출 학생이 없어서 리마인더를 전송하지 않았습니다.", "success": True}
        
        # 슬랙 봇 초기화 및 전송
        try:
            slack_bot = SlackBoltReminderBot()
            
            # 기수별 메시지 생성
            all_non_submitted = []
            cohort_messages = []
            
            for cohort, students in request.non_submitted_by_cohort.items():
                if students:
                    all_non_submitted.extend(students)
                    exam_id = request.cohort_exam_ids.get(cohort, "")
                    cohort_messages.append(f"{cohort}기 (시험 ID: {exam_id}): {len(students)}명")
            
            # 기수별로 구분된 리마인더 전송 (기존 함수 재사용)
            result = slack_bot.send_homework_reminder(
                exam_id=f"기수별 ({', '.join(request.cohort_exam_ids.values())})",
                non_submitted_students=all_non_submitted,
                channel=request.channel
            )
            
            if result['success']:
                return {
                    "message": f"기수별 리마인더: 총 {result['students_count']}명에게 전송했습니다. ({', '.join(cohort_messages)})",
                    "success": True,
                    "channel": result['channel'],
                    "timestamp": result['timestamp']
                }
            else:
                return {
                    "message": f"리마인더 전송 실패: {result['message']}",
                    "success": False
                }
                
        except ValueError as e:
            # 슬랙 봇 토큰이 없는 경우
            return {
                "message": f"슬랙 봇 설정이 필요합니다: {str(e)}",
                "success": False,
                "need_config": True
            }
            
    except Exception as e:
        return {
            "message": f"예상치 못한 오류가 발생했습니다: {str(e)}",
            "success": False
        }

async def run_homework_check_task(cohort_exam_ids: dict):
    """백그라운드에서 실행되는 기수별 과제 확인 작업"""
    global bot_instance, crawl_results
    
    try:
        bot_instance = HomeworkReminderBot()
        
        # 진행률 콜백 함수 (WebSocket 호환)
        def sync_progress_callback(progress: float, desc: str, students: list = None, total: int = 0):
            asyncio.create_task(manager.send_message(json.dumps({
                "type": "progress", 
                "progress": progress / 100.0,  # 0-1 범위로 정규화
                "description": desc,
                "submitted_count": len(students) if students else 0
            })))
            
            # 로그도 함께 전송
            asyncio.create_task(manager.send_message(json.dumps({
                "type": "log",
                "message": desc
            })))
        
        # 과제 확인 시작
        await manager.send_message(json.dumps({
            "type": "log",
            "message": "🚀 기수별 과제 확인 시작..."
        }))
        
        # 새로운 기수별 처리 메서드 호출
        result = bot_instance.run_homework_check_multiple(
            cohort_exam_ids, 
            progress_callback=sync_progress_callback
        )
        
        if not result:
            await manager.send_message(json.dumps({
                "type": "error",
                "message": "과제 확인 프로세스 실행 실패"
            }))
            return
        
        # 결과 저장 (기수별 정보 포함)
        crawl_results = {
            "cohort_exam_ids": result['cohort_exam_ids'],
            "cohort_results": result.get('cohort_results', {}),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "submitted": result['submitted'],
            "non_submitted_by_cohort": result['non_submitted_by_cohort'],
            "total_students": result['total_students'],
            "submitted_count": result['submitted_count'],
            "non_submitted_count": result['non_submitted_count']
        }
        
        # 완료 메시지 전송
        await manager.send_message(json.dumps({
            "type": "complete",
            "message": f"기수별 과제 확인 완료! 제출: {result['submitted_count']}명, 미제출: {result['non_submitted_count']}명",
            "results": crawl_results
        }))
        
    except Exception as e:
        error_message = f"오류 발생: {str(e)}"
        await manager.send_message(json.dumps({
            "type": "log",
            "message": error_message
        }))
        await manager.send_message(json.dumps({
            "type": "error",
            "message": error_message
        }))
    finally:
        if bot_instance:
            bot_instance.cleanup()
        await manager.send_message(json.dumps({
            "type": "log",
            "message": "클린업 완료. 작업 종료."
        }))

if __name__ == "__main__":
    import uvicorn
    
    # 포트 5000이 사용 중인 경우 5001 사용
    import socket
    
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0
    
    port = 5000
    if is_port_in_use(port):
        port = 5001
        print(f"⚠️  포트 5000이 사용 중입니다. 포트 {port}을 사용합니다.")
        print(f"   브라우저에서 http://localhost:{port} 으로 접속하세요.")
    
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)