import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

# URL kết nối mặc định trỏ tới container Docker pgvector chạy cục bộ
DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/postgres"

def get_connection():
    """Tạo kết nối tới cơ sở dữ liệu PostgreSQL."""
    db_url = os.environ.get("DATABASE_URL", DEFAULT_DB_URL)
    try:
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        print(f"[Error] Failed to connect to PostgreSQL at {db_url}: {e}")
        raise e

def initialize_database(schema_path="schema/schema.sql"):
    """Đọc file schema.sql và chạy khởi tạo các bảng nếu chưa tồn tại."""
    if not os.path.exists(schema_path):
        print(f"[Error] Schema SQL file not found at: {schema_path}")
        return False
        
    print(f"Initializing database schema from: {schema_path}...")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            with open(schema_path, "r", encoding="utf-8") as f:
                schema_sql = f.read()
            cur.execute(schema_sql)
        conn.commit()
        print("Database schema initialized successfully.")
        return True
    except Exception as e:
        conn.rollback()
        print(f"[Error] Failed to initialize database: {e}")
        raise e
    finally:
        conn.close()

def save_script(title, niche, raw_text, timeline_json):
    """Lưu thông tin kịch bản vào cơ sở dữ liệu."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO scripts (title, niche, raw_text, timeline_json, status)
                VALUES (%s, %s, %s, %s, 'verified')
                RETURNING id;
            """
            cur.execute(query, (title, niche, raw_text, json.dumps(timeline_json, ensure_ascii=False)))
            script_id = cur.fetchone()[0]
        conn.commit()
        print(f"Saved script '{title}' (ID: {script_id}) to database.")
        return script_id
    except Exception as e:
        conn.rollback()
        print(f"[Error] Failed to save script: {e}")
        raise e
    finally:
        conn.close()

def create_or_get_entity(name, description=""):
    """Tạo mới hoặc lấy thực thể tri thức (Entity Node)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Tìm thực thể cũ
            cur.execute("SELECT id FROM entities WHERE name = %s;", (name,))
            res = cur.fetchone()
            if res:
                return res[0]
                
            # Tạo mới nếu chưa có
            query = """
                INSERT INTO entities (name, description)
                VALUES (%s, %s)
                RETURNING id;
            """
            cur.execute(query, (name, description))
            entity_id = cur.fetchone()[0]
        conn.commit()
        print(f"Created new entity '{name}' (ID: {entity_id}) in Content Graph.")
        return entity_id
    except Exception as e:
        conn.rollback()
        print(f"[Error] Failed to create entity {name}: {e}")
        raise e
    finally:
        conn.close()

def save_asset(entity_id, asset_type, style_preset, storage_path, prompt_text):
    """Lưu trữ tệp hình ảnh/âm thanh liên kết với thực thể vào database."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO assets (entity_id, asset_type, style_preset, storage_path, prompt_text)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING id;
            """
            cur.execute(query, (entity_id, asset_type, style_preset, storage_path, prompt_text))
            asset_id = cur.fetchone()[0]
        conn.commit()
        print(f"Saved asset {asset_type} (ID: {asset_id}) linked to Entity ID {entity_id}.")
        return asset_id
    except Exception as e:
        conn.rollback()
        print(f"[Error] Failed to save asset: {e}")
        raise e
    finally:
        conn.close()

def create_or_get_channel(name, platform):
    """Tạo mới hoặc lấy một kênh xuất bản nội dung theo nền tảng."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM channels WHERE name = %s AND platform = %s;", (name, platform))
            res = cur.fetchone()
            if res:
                return res[0]
                
            query = """
                INSERT INTO channels (name, platform, channel_url)
                VALUES (%s, %s, %s)
                RETURNING id;
            """
            url = f"https://{platform}.com/{name.lower().replace(' ', '')}"
            cur.execute(query, (name, platform, url))
            channel_id = cur.fetchone()[0]
        conn.commit()
        print(f"Channel created: '{name}' on '{platform}' (ID: {channel_id}).")
        return channel_id
    except Exception as e:
        conn.rollback()
        print(f"[Error] Failed to create channel {name}: {e}")
        raise e
    finally:
        conn.close()

def save_video(script_id, filepath, status="rendered", channel_id=None, platform_video_id=None):
    """Lưu thông tin video thành phẩm hoặc trạng thái xuất bản."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            query = """
                INSERT INTO videos (script_id, filepath, status, channel_id, platform_video_id, published_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """
            import datetime
            pub_date = datetime.datetime.now() if status == "published" else None
            cur.execute(query, (script_id, filepath, status, channel_id, platform_video_id, pub_date))
            video_id = cur.fetchone()[0]
        conn.commit()
        print(f"Saved video metadata (ID: {video_id}) for Script ID {script_id} with status {status}.")
        return video_id
    except Exception as e:
        conn.rollback()
        print(f"[Error] Failed to save video: {e}")
        raise e
    finally:
        conn.close()

def get_database_summary():
    """Truy vấn lấy tổng hợp báo cáo từ cơ sở dữ liệu để in ra console nghiệm thu."""
    conn = get_connection()
    summary = []
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # 1. Thống kê kịch bản
            cur.execute("SELECT id, title, niche, status, created_at FROM scripts ORDER BY id DESC LIMIT 5;")
            scripts = cur.fetchall()
            summary.append("\n=== LATEST SCRIPTS IN DATABASE ===")
            for s in scripts:
                summary.append(f"ID: {s['id']} | Title: {s['title']} | Niche: {s['niche']} | Created: {s['created_at']}")
                
            # 2. Thống kê thực thể (Entities)
            cur.execute("SELECT id, name, created_at FROM entities ORDER BY id DESC LIMIT 5;")
            entities = cur.fetchall()
            summary.append("\n=== LATEST ENTITIES IN CONTENT GRAPH ===")
            for e in entities:
                summary.append(f"ID: {e['id']} | Name: {e['name']} | Created: {e['created_at']}")
                
            # 3. Thống kê Assets
            cur.execute("SELECT a.id, e.name as entity_name, a.asset_type, a.storage_path FROM assets a LEFT JOIN entities e ON a.entity_id = e.id ORDER BY a.id DESC LIMIT 5;")
            assets = cur.fetchall()
            summary.append("\n=== LATEST ASSETS IN DATABASE ===")
            for a in assets:
                summary.append(f"ID: {a['id']} | Type: {a['asset_type']} | Entity: {a['entity_name']} | Path: {a['storage_path']}")
                
            # 4. Thống kê Kênh Xuất Bản (Channels)
            cur.execute("SELECT id, name, platform FROM channels ORDER BY id DESC LIMIT 5;")
            channels = cur.fetchall()
            if channels:
                summary.append("\n=== CHANNELS IN DATABASE ===")
                for c in channels:
                    summary.append(f"ID: {c['id']} | Name: {c['name']} | Platform: {c['platform']}")

            # 5. Thống kê Videos & Trạng thái xuất bản
            cur.execute("""
                SELECT v.id, s.title as script_title, c.platform, v.status, v.platform_video_id 
                FROM videos v 
                JOIN scripts s ON v.script_id = s.id 
                LEFT JOIN channels c ON v.channel_id = c.id
                ORDER BY v.id DESC LIMIT 8;
            """)
            videos = cur.fetchall()
            summary.append("\n=== LATEST COMPOSER & PUBLISHED VIDEOS ===")
            for v in videos:
                platform_str = f"Platform: {v['platform']}" if v['platform'] else "Local Only"
                video_id_str = f" | ID: {v['platform_video_id']}" if v['platform_video_id'] else ""
                summary.append(f"ID: {v['id']} | Status: {v['status']} | {platform_str}{video_id_str} | Script: {v['script_title']}")
                
        return "\n".join(summary)
    except Exception as e:
        print(f"[Error] Failed to generate database summary: {e}")
        return "Failed to query database summary."
    finally:
        conn.close()
