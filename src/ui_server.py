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

from agents.script_writer import generate_script_timeline
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
        print(f"[Web Server] Generating script draft using provider: '{req.provider}'")
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

@app.post("/api/render-video")
async def render_video_api(req: RenderRequest):
    """BƯỚC 2: Nhận kịch bản đã biên tập từ người dùng, lưu database và chạy render."""
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
        
        # Chạy render video bằng FFmpeg
        print("[Web Server] Rendering video from edited timeline...")
        compose_video(timeline_path, output_path)
        
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
        db_summary = get_database_summary()
        
        return {
            "status": "success",
            "video_url": "/static/output.mp4",
            "db_summary": db_summary,
            "script_id": script_id,
            "filepath": os.path.abspath(output_path),
            "message": "Video rendered and archived successfully!"
        }
        
    except Exception as e:
        import traceback
        trace = traceback.format_exc()
        print(f"[Render API Error] {e}\n{trace}")
        return {"status": "error", "message": str(e), "traceback": trace}

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
