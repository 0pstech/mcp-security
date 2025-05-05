import sys
import logging
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# CORS 미들웨어 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발용: 모든 origin 허용. 운영시에는 도메인 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

LOG_DIR = Path("/Users/j/Library/Logs/Claude")


def get_latest_logfile():
    log_files = sorted(LOG_DIR.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    return log_files[0] if log_files else None


def read_last_n_lines(file_path, n=100):
    """파일의 마지막 n줄을 반환"""
    with open(file_path, "r") as f:
        return f.readlines()[-n:]


async def event_generator(request):
    """SSE generator for the latest log file."""
    latest_log = get_latest_logfile()
    if not latest_log:
        yield {"event": "error", "data": "No log file found."}
        return
    logger.info(f"Streaming log file: {latest_log}")

    # 1. 기존 마지막 100줄 먼저 전송
    for line in read_last_n_lines(latest_log, 100):
        if await request.is_disconnected():
            logger.info("SSE client disconnected.")
            return
        yield {"event": "log", "data": line.rstrip()}

    # 2. 그 이후부터는 tail 방식으로 새로 추가되는 줄만 전송
    with open(latest_log, "r") as f:
        f.seek(0, 2)  # 파일 끝으로 이동
        while True:
            if await request.is_disconnected():
                logger.info("SSE client disconnected.")
                break
            line = f.readline()
            if line:
                yield {"event": "log", "data": line.rstrip()}
            else:
                await asyncio.sleep(0.5)


@app.get("/logs")
async def logs():
    files = sorted(LOG_DIR.glob("*.log"), key=lambda f: f.stat().st_mtime, reverse=True)
    return JSONResponse([f.name for f in files])


@app.get("/sse")
async def sse_endpoint(request: Request):
    """SSE endpoint for real-time log streaming."""
    return EventSourceResponse(event_generator(request))


if __name__ == "__main__":
    logger.info("Starting Claude log SSE server...")
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
