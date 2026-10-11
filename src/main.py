import os
import sys
import json
import argparse
import traceback

# Thêm thư mục hiện tại vào Python Path để import thuận tiện
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.script_writer import generate_script_timeline
from db.manager import initialize_database, save_script, create_or_get_entity, save_asset, save_video, get_database_summary
from render.video_composer import compose_video

def main():
    parser = argparse.ArgumentParser(description="AI Content Factory End-to-End Pipeline")
    parser.add_argument("--topic", type=str, default="Sự thật kinh ngạc về hố đen vũ trụ", help="Chủ đề muốn làm video")
    parser.add_argument("--provider", type=str, default="local", help="AI provider (local, gemini, openai, claude)")
    parser.add_argument("--api-key", type=str, default="", help="API key hoặc tên model cục bộ của Ollama (ví dụ: glm-5.2)")
    args = parser.parse_args()
    
    topic = args.topic
    provider = args.provider.strip().lower()
    api_key = args.api_key.strip()
    
    # Thiết lập mặc định cho api_key nếu trống
    if not api_key:
        if provider == "local":
            api_key = "glm-5.2"
        elif provider == "openai":
            api_key = os.environ.get("OPENAI_API_KEY", "")
        elif provider == "gemini":
            api_key = os.environ.get("GEMINI_API_KEY", "")
        elif provider == "claude":
            api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    timeline_path = "src/timeline_example.json"
    output_path = "output.mp4"
    
    print("==================================================")
    print("      AI CONTENT FACTORY - INTEGRATED PIPELINE    ")
    print("==================================================")
    print(f"Topic: {topic}")
    print(f"Provider: {provider}")
    print(f"API Key / Model: {api_key[:8]}..." if len(api_key) > 8 else f"API Key / Model: {api_key}")
    
    # 1. Kiểm tra API Key / cấu hình hợp lệ
    if provider != "local" and not api_key:
        print(f"\n[Error] Khóa API cho provider '{provider}' chưa được thiết lập!")
        print("Vui lòng thiết lập biến môi trường hoặc chạy kèm tham số --api-key.")
        sys.exit(1)
        
    # Set env var if needed by library inside agent
    if provider == "openai":
        os.environ["OPENAI_API_KEY"] = api_key
    elif provider == "claude":
        os.environ["ANTHROPIC_API_KEY"] = api_key
        
    # 2. Khởi động và kết nối Database PostgreSQL
    print("\n--- STEP 1: INITIALIZING POSTGRESQL DATABASE ---")
    try:
        initialize_database("schema/schema.sql")
    except Exception as e:
        print("\n[Error] Không thể kết nối hoặc khởi tạo cơ sở dữ liệu PostgreSQL!")
        print("Để chạy kiểm thử khâu này, vui lòng bật Docker và khởi động container pgvector:")
        print("   docker run --name content-creator-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d pgvector/pgvector:pg16")
        print("\nHoặc thiết lập biến môi trường DATABASE_URL để kết nối tới DB hiện có của bạn:")
        print("   $env:DATABASE_URL=\"postgresql://user:pass@host:port/dbname\"")
        sys.exit(1)
        
    # 3. Biên kịch tự động bằng AI Agent (Khâu A)
    print("\n--- STEP 2: GENERATING SCRIPT AND TIMELINE WITH AI AGENT ---")
    try:
        timeline = generate_script_timeline(
            topic=topic,
            provider=provider,
            api_key=api_key
        )
        # Lưu nháp file JSON timeline
        with open(timeline_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
        print("AI Script Writer finished. Storyboard JSON successfully generated.")
    except Exception as e:
        print(f"\n[Error] Gặp lỗi khi sinh kịch bản từ AI: {e}")
        traceback.print_exc()
        sys.exit(1)
        
    # 4. Lưu Kịch Bản vào Database (Khâu B)
    print("\n--- STEP 3: SAVING SCRIPT METADATA TO DATABASE ---")
    try:
        # Gộp toàn bộ thuyết minh các cảnh để lưu kịch bản thô
        raw_text = "\n".join([scene["voice_text"] for scene in timeline["scenes"]])
        script_id = save_script(
            title=timeline["project_title"],
            niche=timeline.get("visual_style", "general"),
            raw_text=raw_text,
            timeline_json=timeline
        )
        
        # Tạo hoặc lấy Thực thể chính (Entity) liên quan đến đề tài này
        entity_id = create_or_get_entity(
            name=timeline["project_title"],
            description=f"Thực thể chính cho đề tài: {topic}"
        )
    except Exception as e:
        print(f"\n[Error] Gặp lỗi khi lưu kịch bản vào Database: {e}")
        sys.exit(1)
        
    # 5. Dựng Video bằng FFmpeg
    print("\n--- STEP 4: COMPOSING VIDEO (TTS + IMAGE + RENDER) ---")
    try:
        compose_video(timeline_path, output_path)
        
        # Load lại file timeline để lấy các đường dẫn âm thanh/hình ảnh thực tế đã được sinh persistent
        with open(timeline_path, 'r', encoding='utf-8') as f:
            updated_timeline = json.load(f)
    except Exception as e:
        print(f"\n[Error] Quá trình dựng video thất bại: {e}")
        traceback.print_exc()
        sys.exit(1)
        
    # 6. Lưu trữ Assets đã sinh và Video thành phẩm vào Database (Khâu B)
    print("\n--- STEP 5: SAVING GENERATED ASSETS & VIDEO METADATA TO DATABASE ---")
    try:
        # Lưu từng asset (ảnh, voice) của từng scene vào bảng assets liên kết với Entity
        for scene in updated_timeline["scenes"]:
            # Lưu voice asset
            save_asset(
                entity_id=entity_id,
                asset_type="voice_audio",
                style_preset=None,
                storage_path=scene["voice_audio_path"],
                prompt_text=scene["voice_text"]
            )
            # Lưu image asset
            save_asset(
                entity_id=entity_id,
                asset_type="image_scene",
                style_preset=updated_timeline.get("visual_style"),
                storage_path=scene["visual_asset_path"],
                prompt_text=scene.get("visual_prompt", scene["voice_text"])
            )
            
        # Lưu video thành phẩm
        save_video(
            script_id=script_id,
            filepath=os.path.abspath(output_path),
            status="rendered"
        )
        print("All generated assets and final video metadata successfully stored in Database.")
    except Exception as e:
        print(f"\n[Error] Gặp lỗi khi lưu trữ tài nguyên vào Database: {e}")
        sys.exit(1)
        
    # 7. Truy vấn in báo cáo SQL ra màn hình kiểm chứng
    print("\n--- STEP 6: QUERYING DATABASE SUMMARY REPORT (VERIFICATION) ---")
    try:
        report = get_database_summary()
        print(report)
        print("\n" + "="*50)
        print("AI CONTENT FACTORY END-TO-END PIPELINE COMPLETED SUCCESSFULLY!")
        print(f"Video file ready at: {os.path.abspath(output_path)}")
        print("="*50)
    except Exception as e:
        print(f"[Error] Failed to print DB summary: {e}")

if __name__ == "__main__":
    main()
