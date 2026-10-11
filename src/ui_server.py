import os
import sys
import shutil
import json
import random
import threading
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Thêm thư mục src vào PATH của Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.script_writer import generate_script_timeline, generate_long_script_timeline
from agents.competitor_scraper import get_trending_ideas
from db.manager import (
    initialize_database, 
    save_script, 
    create_or_get_entity, 
    save_asset, 
    save_video, 
    create_or_get_channel,
    get_database_summary
)
from render.video_composer import compose_video

app = FastAPI(title="AI Content Factory Local UI")

# Khởi tạo các thư mục lưu trữ web tĩnh
os.makedirs("src/web/static", exist_ok=True)
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Bộ nhớ đệm cache ý tưởng để hiển thị tức thì khi tải trang
cached_ideas = []

@app.on_event("startup")
def prefetch_ideas_on_startup():
    """Tải trước danh sách ý tưởng hot ngầm lúc khởi động."""
    def worker():
        global cached_ideas
        try:
            print("[Startup] Pre-fetching popular competitor ideas...")
            cached_ideas = get_trending_ideas("Bí ẩn lịch sử khoa học")
            print("[Startup] Competitor ideas pre-loaded successfully.")
        except Exception as e:
            print(f"[Startup Error] Failed to pre-fetch: {e}")
    threading.Thread(target=worker, daemon=True).start()

class ScriptRequest(BaseModel):
    topic: str
    openai_key: str
    provider: str
    feedback: str = ""
    duration: str = "short"

class RenderRequest(BaseModel):
    timeline: dict  # Nhận kịch bản JSON đã được chỉnh sửa thủ công từ UI
    db_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    sd_url: str = "http://localhost:7860"

class PublishRequest(BaseModel):
    script_id: int
    filepath: str
    platforms: list[str]
    db_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"

@app.get("/api/scrape-ideas")
async def scrape_ideas_api(keyword: str = "Bí ẩn lịch sử khoa học"):
    """API cào tìm các ý tưởng hot từ đối thủ."""
    global cached_ideas
    try:
        if keyword == "Bí ẩn lịch sử khoa học" and cached_ideas:
            return {"status": "success", "ideas": cached_ideas}
            
        ideas = get_trending_ideas(keyword)
        return {"status": "success", "ideas": ideas}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-script")
async def generate_script_api(req: ScriptRequest):
    """BƯỚC 1: Sáng tác kịch bản nháp (JSON) và gửi về UI để biên tập."""
    os.environ["OPENAI_API_KEY"] = req.openai_key.strip()
    
    try:
        print(f"[Web Server] Generating script draft using provider: '{req.provider}' (duration: {req.duration})")
        if req.duration == "long":
            timeline = generate_long_script_timeline(
                topic=req.topic,
                provider=req.provider,
                api_key=req.openai_key,
                feedback=req.feedback
            )
        else:
            timeline = generate_script_timeline(
                topic=req.topic,
                provider=req.provider,
                api_key=req.openai_key,
                feedback=req.feedback
            )
        return {"status": "success", "timeline": timeline}
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print(f"[Script API Error] {e}\n{trace}")
        return {"status": "error", "message": str(e), "traceback": trace}
# Trạng thái tiến độ dựng video toàn cục
render_status = {
    "status": "idle",
    "percent": 0,
    "message": ""
}

def run_render_in_background(timeline_path: str, output_path: str, static_output_path: str, script_id: int, entity_id: int, timeline: dict):
    global render_status
    try:
        def progress_callback(percent: int, message: str):
            global render_status
            render_status = {
                "status": "rendering" if percent < 100 else "success",
                "percent": percent,
                "message": message
            }
            print(f"[Render Progress {percent}%] {message}")

        # Chạy dựng video
        compose_video(timeline_path, output_path, progress_callback=progress_callback)
        
        # Đọc lại kịch bản cập nhật chứa các link assets
        with open(timeline_path, 'r', encoding='utf-8') as f:
            updated_timeline = json.load(f)
            
        # Lưu danh sách Assets và Video vào PostgreSQL
        print("[Web Server] Archiving assets to DB...")
        for scene in updated_timeline["scenes"]:
            save_asset(entity_id, "voice_audio", None, scene["voice_audio_path"], scene["voice_text"])
            asset_type = "chart_scene" if scene.get("chart_data") else "image_scene"
            save_asset(entity_id, asset_type, updated_timeline.get("visual_style"), scene["visual_asset_path"], scene.get("visual_prompt", scene["voice_text"]))
            
        save_video(script_id, os.path.abspath(output_path), "rendered")
        
        # Copy video thành phẩm sang static web
        shutil.copy(output_path, static_output_path)
        
        render_status = {
            "status": "success",
            "percent": 100,
            "message": "Hoàn tất dựng video thành công!"
        }
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print(f"[Render Background Error] {e}\n{trace}")
        render_status = {
            "status": "error",
            "percent": 0,
            "message": f"Lỗi dựng video: {str(e)}"
        }

@app.post("/api/render-video")
async def render_video_api(req: RenderRequest):
    """BƯỚC 2: Nhận kịch bản đã biên tập từ người dùng, lưu database và kích hoạt render ngầm."""
    global render_status
    os.environ["DATABASE_URL"] = req.db_url.strip()
    os.environ["SD_API_URL"] = req.sd_url.strip()
    os.environ["PYTHONUTF8"] = "1"
    
    timeline_path = "src/timeline_example.json"
    output_path = "output.mp4"
    static_output_path = "src/web/static/output.mp4"
    
    try:
        # Khởi tạo database
        print("[Web Server] Initializing Database...")
        initialize_database("schema/schema.sql")
        
        # Ghi kịch bản đã chỉnh sửa ra đĩa để FFmpeg đọc
        timeline = req.timeline
        with open(timeline_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
            
        # Lưu kịch bản vào PostgreSQL
        print("[Web Server] Saving edited script to DB...")
        raw_text = "\n".join([scene["voice_text"] for scene in timeline["scenes"]])
        script_id = save_script(timeline["project_title"], timeline.get("visual_style", "general"), raw_text, timeline)
        entity_id = create_or_get_entity(timeline["project_title"], f"Main entity for video: {timeline['project_title']}")
        
        # Thiết lập trạng thái ban đầu và chạy nền
        render_status = {
            "status": "rendering",
            "percent": 0,
            "message": "Khởi tạo luồng sinh ảnh và thuyết minh..."
        }
        
        threading.Thread(
            target=run_render_in_background,
            args=(timeline_path, output_path, static_output_path, script_id, entity_id, timeline),
            daemon=True
        ).start()
        
        return {
            "status": "started",
            "message": "Video rendering started in the background."
        }
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print(f"[Render API Error] {e}\n{trace}")
        return {"status": "error", "message": str(e), "traceback": trace}

@app.get("/api/render-status")
async def render_status_api():
    """Lấy trạng thái tiến độ dựng video hiện tại."""
    global render_status
    db_summary = ""
    if render_status["status"] == "success":
        try:
            db_summary = get_database_summary()
        except Exception:
            db_summary = "Không thể đọc tóm tắt DB."
            
    return {
        "status": render_status["status"],
        "percent": render_status["percent"],
        "message": render_status["message"],
        "db_summary": db_summary
    }

@app.post("/api/publish")
async def publish_video_api(req: PublishRequest):
    """API giả lập đăng tải video lên các nền tảng được chọn."""
    os.environ["DATABASE_URL"] = req.db_url.strip()
    
    if not req.platforms:
        raise HTTPException(status_code=400, detail="No publishing platforms selected.")
        
    logs = []
    try:
        for platform in req.platforms:
            print(f"[Web Server] Simulating upload to {platform}...")
            channel_name = f"Factory Publisher ({platform.capitalize()})"
            channel_id = create_or_get_channel(channel_name, platform)
            
            prefix = platform[:2].lower()
            mock_video_id = f"{prefix}_v_{random.randint(100000, 999999)}"
            
            save_video(
                script_id=req.script_id,
                filepath=req.filepath,
                status="published",
                channel_id=channel_id,
                platform_video_id=mock_video_id
            )
            logs.append(f"✓ Successfully published to {platform.upper()} (Mock ID: {mock_video_id})")
            
        db_summary = get_database_summary()
        return {
            "status": "success",
            "message": "\n".join(logs),
            "db_summary": db_summary
        }
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print(f"[Publish Server Error] {e}\n{trace}")
        return {
            "status": "error",
            "message": f"Publishing failed: {e}",
            "traceback": trace
        }

@app.get("/api/db-summary")
async def db_summary_api():
    """Lấy báo cáo truy vấn cơ sở dữ liệu mới nhất."""
    try:
        summary = get_database_summary()
        return {"summary": summary}
    except Exception as e:
        return {"summary": f"Could not query database. Ensure your Postgres is running. Details: {e}"}

# Đăng ký thư mục static
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

@app.get("/")
async def get_index():
    """Trả về giao diện HTML chính."""
    index_path = "src/web/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail="index.html template not found")

if __name__ == "__main__":
    import uvicorn
    print("Launching AI Content Factory local server on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
