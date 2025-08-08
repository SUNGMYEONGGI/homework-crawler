from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
import asyncio
import json
import os
import time
import importlib.util


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_module_from_path(module_name: str, file_path: str):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


# Absolute paths to existing systems
REMINDER_MAIN_PATH = \
    "/Users/seongmyeong-gi/Desktop/project/homework-reminder-bot/main.py"
REMINDER_SLACK_PATH = \
    "/Users/seongmyeong-gi/Desktop/project/homework-reminder-bot/slack_bolt_bot.py"
CRAWLER_PATH = \
    "/Users/seongmyeong-gi/Desktop/project/homework-crawler/fastcampus-crawler-api/crawler.py"


# Load external modules safely with unique names to avoid conflicts (optional)
REMINDER_AVAILABLE = True
CRAWLER_AVAILABLE = True

try:
    reminder_main = load_module_from_path("reminder_main", REMINDER_MAIN_PATH)
    HomeworkReminderBot = getattr(reminder_main, "HomeworkReminderBot")
except Exception:
    REMINDER_AVAILABLE = False
    # Fallback stub
    class HomeworkReminderBot:  # type: ignore
        def __init__(self):
            self.driver = None
            self.log_messages = []
        def run_homework_check_multiple(self, *_args, **_kwargs):
            raise RuntimeError("리마인더 모듈이 설치되어 있지 않습니다.")
        def cleanup(self):
            self.driver = None

try:
    reminder_slack = load_module_from_path("reminder_slack", REMINDER_SLACK_PATH)
    SlackBoltReminderBot = getattr(reminder_slack, "SlackBoltReminderBot")
except Exception:
    # Slack 전송 기능만 비활성화될 수 있으므로 별도 플래그가 있으면 좋지만, 간단히 REMINDER_AVAILABLE에 포함시키지 않음
    SlackBoltReminderBot = None  # type: ignore

try:
    crawler_module = load_module_from_path("crawler_module", CRAWLER_PATH)
    FastCampusLMSCrawler = getattr(crawler_module, "FastCampusLMSCrawler")
except Exception:
    CRAWLER_AVAILABLE = False
    class FastCampusLMSCrawler:  # type: ignore
        def __init__(self):
            self.is_running = False
            self.current_exam_id = None
        def login_process(self):
            raise RuntimeError("크롤러 모듈이 설치되어 있지 않습니다.")
        async def crawl_exam_data_async(self, *_args, **_kwargs):
            return 0
        def export_data(self, *_args, **_kwargs):
            return None
        def cleanup(self):
            self.is_running = False


app = FastAPI(title="Homework All-in-One", version="1.0.0")

# Serve static assets
STATIC_DIR = os.path.join(BASE_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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
        stale = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                stale.append(connection)
        # Cleanup stale connections
        for s in stale:
            if s in self.active_connections:
                self.active_connections.remove(s)


# Managers (separate channels per subsystem)
reminder_manager = ConnectionManager()
crawler_manager = ConnectionManager()


# Global states (kept minimal and explicit)
reminder_bot_instance = None
reminder_results = {}

crawler_instance = None


# ===== Models =====
class ReminderCrawlRequest(BaseModel):
    cohort_13: Optional[str] = ""
    cohort_14: Optional[str] = ""
    cohort_15: Optional[str] = ""
    cohort_16: Optional[str] = ""


class SlackRequest(BaseModel):
    cohort_exam_ids: dict
    non_submitted_by_cohort: dict
    channel: Optional[str] = None


class CrawlerCrawlRequest(BaseModel):
    exam_id: str
    file_format: str = "csv"  # csv | xlsx | json | xml


# ===== Root Page =====
@app.get("/")
async def root_page():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/availability")
async def availability():
    return {
        "reminder": REMINDER_AVAILABLE,
        "reminder_slack": bool(SlackBoltReminderBot),
        "crawler": CRAWLER_AVAILABLE,
    }


# ===== Reminder WS =====
@app.websocket("/reminder/ws")
async def reminder_ws(websocket: WebSocket):
    await reminder_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        reminder_manager.disconnect(websocket)


# ===== Crawler WS =====
@app.websocket("/crawler/ws")
async def crawler_ws(websocket: WebSocket):
    await crawler_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        crawler_manager.disconnect(websocket)


# ===== Reminder APIs =====
@app.post("/reminder/api/check_homework")
async def reminder_check(request: ReminderCrawlRequest, background_tasks: BackgroundTasks):
    if not REMINDER_AVAILABLE:
        raise HTTPException(status_code=503, detail="리마인더 기능이 설치되어 있지 않습니다.")
    global reminder_bot_instance

    cohort_exam_ids = {
        "13": (request.cohort_13 or "").strip(),
        "14": (request.cohort_14 or "").strip(),
        "15": (request.cohort_15 or "").strip(),
        "16": (request.cohort_16 or "").strip(),
    }

    valid_exams = [v for v in cohort_exam_ids.values() if v]
    if not valid_exams:
        raise HTTPException(status_code=400, detail="최소 하나의 기수에 대한 시험 ID를 입력해주세요.")

    if reminder_bot_instance and hasattr(reminder_bot_instance, "driver") and reminder_bot_instance.driver:
        raise HTTPException(status_code=409, detail="이미 다른 크롤링 작업이 실행 중입니다.")

    background_tasks.add_task(_run_reminder_task, cohort_exam_ids)
    return {"message": "과제 확인을 시작했습니다.", "cohort_exam_ids": cohort_exam_ids}


@app.post("/reminder/api/stop")
async def reminder_stop():
    if not REMINDER_AVAILABLE:
        return {"message": "리마인더 모듈이 없어 중지할 작업이 없습니다."}
    global reminder_bot_instance
    if not reminder_bot_instance or not getattr(reminder_bot_instance, "driver", None):
        return {"message": "현재 실행 중인 크롤링 작업이 없습니다."}
    reminder_bot_instance.cleanup()
    await reminder_manager.send_message(json.dumps({"type": "info", "message": "크롤링 중지 요청됨. 드라이버가 종료되었습니다."}))
    return {"message": "크롤링이 중지되었습니다."}


@app.get("/reminder/api/status")
async def reminder_status():
    global reminder_bot_instance
    is_running = bool(reminder_bot_instance and getattr(reminder_bot_instance, "driver", None))
    return {"is_running": is_running, "current_exam_id": getattr(reminder_bot_instance, "current_exam_id", None) if reminder_bot_instance else None}


@app.get("/reminder/api/results")
async def reminder_get_results():
    return reminder_results


@app.get("/reminder/api/logs")
async def reminder_get_logs():
    global reminder_bot_instance
    logs = []
    if reminder_bot_instance and hasattr(reminder_bot_instance, "log_messages"):
        logs = reminder_bot_instance.log_messages[-20:]
    return {"logs": logs}


@app.post("/reminder/api/send_slack_reminder")
async def reminder_send_slack(request: SlackRequest):
    if not SlackBoltReminderBot:
        return {"message": "슬랙 기능이 비활성화되어 있습니다.", "success": False}
    try:
        total_non_submitted = sum(len(v) for v in request.non_submitted_by_cohort.values())
        if total_non_submitted == 0:
            return {"message": "미제출 학생이 없어서 리마인더를 전송하지 않았습니다.", "success": True}

        slack_bot = SlackBoltReminderBot()

        all_non_submitted = []
        cohort_messages = []
        for cohort, students in request.non_submitted_by_cohort.items():
            if students:
                all_non_submitted.extend(students)
                exam_id = request.cohort_exam_ids.get(cohort, "")
                cohort_messages.append(f"{cohort}기 (시험 ID: {exam_id}): {len(students)}명")

        result = slack_bot.send_homework_reminder(
            exam_id=f"기수별 ({', '.join(request.cohort_exam_ids.values())})",
            non_submitted_students=all_non_submitted,
            channel=request.channel,
        )

        if result.get("success"):
            return {
                "message": f"기수별 리마인더: 총 {result['students_count']}명에게 전송했습니다. ({', '.join(cohort_messages)})",
                "success": True,
                "channel": result.get("channel"),
                "timestamp": result.get("timestamp"),
            }
        else:
            return {"message": f"리마인더 전송 실패: {result.get('message')}", "success": False}
    except ValueError as e:
        return {"message": f"슬랙 봇 설정이 필요합니다: {str(e)}", "success": False, "need_config": True}
    except Exception as e:
        return {"message": f"예상치 못한 오류가 발생했습니다: {str(e)}", "success": False}


async def _run_reminder_task(cohort_exam_ids: dict):
    global reminder_bot_instance, reminder_results
    try:
        reminder_bot_instance = HomeworkReminderBot()

        def sync_progress_callback(progress: float, desc: str, students: list | None = None, total: int = 0):
            # Normalize progress to 0-1 for UI consistency
            asyncio.create_task(reminder_manager.send_message(json.dumps({
                "type": "progress",
                "progress": progress / 100.0,
                "description": desc,
                "submitted_count": len(students) if students else 0,
            })))
            asyncio.create_task(reminder_manager.send_message(json.dumps({"type": "log", "message": desc})))

        await reminder_manager.send_message(json.dumps({"type": "log", "message": "🚀 기수별 과제 확인 시작..."}))

        result = reminder_bot_instance.run_homework_check_multiple(cohort_exam_ids, progress_callback=sync_progress_callback)
        if not result:
            await reminder_manager.send_message(json.dumps({"type": "error", "message": "과제 확인 프로세스 실행 실패"}))
            return

        reminder_results = {
            "cohort_exam_ids": result["cohort_exam_ids"],
            "cohort_results": result.get("cohort_results", {}),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "submitted": result["submitted"],
            "non_submitted_by_cohort": result["non_submitted_by_cohort"],
            "total_students": result["total_students"],
            "submitted_count": result["submitted_count"],
            "non_submitted_count": result["non_submitted_count"],
        }

        await reminder_manager.send_message(json.dumps({
            "type": "complete",
            "message": f"기수별 과제 확인 완료! 제출: {result['submitted_count']}명, 미제출: {result['non_submitted_count']}명",
            "results": reminder_results,
        }))
    except Exception as e:
        error_message = f"오류 발생: {str(e)}"
        await reminder_manager.send_message(json.dumps({"type": "log", "message": error_message}))
        await reminder_manager.send_message(json.dumps({"type": "error", "message": error_message}))
    finally:
        if reminder_bot_instance:
            reminder_bot_instance.cleanup()
        await reminder_manager.send_message(json.dumps({"type": "log", "message": "클린업 완료. 작업 종료."}))


# ===== Crawler APIs =====
@app.post("/crawler/api/crawl")
async def crawler_start(request: CrawlerCrawlRequest, background_tasks: BackgroundTasks):
    if not CRAWLER_AVAILABLE:
        raise HTTPException(status_code=503, detail="크롤러 기능이 설치되어 있지 않습니다.")
    global crawler_instance
    if not request.exam_id.isdigit():
        raise HTTPException(status_code=400, detail="올바른 시험 ID(숫자)를 입력하세요.")
    if crawler_instance and getattr(crawler_instance, "is_running", False):
        raise HTTPException(status_code=409, detail="이미 다른 크롤링 작업이 실행 중입니다.")
    background_tasks.add_task(_run_crawling_task, request.exam_id, request.file_format)
    return {"message": "크롤링이 시작되었습니다.", "exam_id": request.exam_id}


@app.post("/crawler/api/stop")
async def crawler_stop():
    if not CRAWLER_AVAILABLE:
        return {"message": "크롤러 모듈이 없어 중지할 작업이 없습니다."}
    global crawler_instance
    if not crawler_instance or not getattr(crawler_instance, "is_running", False):
        return {"message": "현재 실행 중인 크롤링 작업이 없습니다."}
    crawler_instance.cleanup()
    await crawler_manager.send_message(json.dumps({"type": "info", "message": "크롤링 중지 요청됨. 드라이버가 종료되었습니다."}))
    return {"message": "크롤링이 중지되었습니다."}


@app.get("/crawler/api/status")
async def crawler_status():
    global crawler_instance
    if not crawler_instance:
        return {"is_running": False, "current_exam_id": None}
    return {"is_running": getattr(crawler_instance, "is_running", False), "current_exam_id": getattr(crawler_instance, "current_exam_id", None)}


@app.get("/crawler/api/download/{filename}")
async def crawler_download(filename: str):
    file_path = filename
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
    return FileResponse(path=file_path, filename=filename, media_type="application/octet-stream")


async def _run_crawling_task(exam_id: str, file_format: str):
    global crawler_instance
    try:
        crawler_instance = FastCampusLMSCrawler()

        async def log_callback(message: str):
            await crawler_manager.send_message(json.dumps({"type": "log", "message": message}))

        async def progress_callback(progress: float, desc: str):
            await crawler_manager.send_message(json.dumps({"type": "progress", "progress": progress, "description": desc}))

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
                await log_callback(f"크롤링 완료! 총 {collected_count}개의 데이터가 수집되어 '{file_path}' 파일에 저장되었습니다.")
                await crawler_manager.send_message(json.dumps({
                    "type": "complete",
                    "message": f"크롤링 완료! {collected_count}개 데이터 수집됨",
                    "file_path": file_path,
                    "count": collected_count,
                }))
            else:
                await log_callback(f"데이터 수집은 완료되었으나 파일 생성에 실패했습니다 (형식: {file_format}).")
                await crawler_manager.send_message(json.dumps({"type": "error", "message": f"파일 생성 실패 (형식: {file_format})"}))
        else:
            await log_callback(f"데이터를 수집하지 못했습니다. (시험 ID: {exam_id})")
            await crawler_manager.send_message(json.dumps({"type": "error", "message": f"데이터 수집 실패 (시험 ID: {exam_id})"}))

        await progress_callback(1.0, "작업 완료")
    except Exception as e:
        error_message = f"오류 발생: {str(e)}"
        async def _safe():
            await crawler_manager.send_message(json.dumps({"type": "log", "message": error_message}))
            await crawler_manager.send_message(json.dumps({"type": "error", "message": error_message}))
        await _safe()
    finally:
        if crawler_instance:
            crawler_instance.cleanup()
        async def _done():
            await crawler_manager.send_message(json.dumps({"type": "log", "message": "클린업 완료. 작업 종료."}))
        await _done()


if __name__ == "__main__":
    import uvicorn
    # Prefer 9000; if in use, fallback to 9001
    def is_port_in_use(port: int) -> bool:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(("localhost", port)) == 0

    port = 9000
    if is_port_in_use(port):
        port = 9001
        print(f"⚠️  포트 9000이 사용 중입니다. 포트 {port}를 사용합니다.")
        print(f"   브라우저에서 http://localhost:{port} 으로 접속하세요.")
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)


