-- Khởi tạo extension pgvector cho việc tìm kiếm vector embeddings
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Bảng Entities: Lưu trữ thực thể tri thức (Content Graph Nodes)
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    description_vector vector(1536), -- Kích thước vector của OpenAI text-embedding-ada-002
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng Entity Relations: Lưu mối quan hệ giữa các thực thể (Content Graph Edges)
CREATE TABLE IF NOT EXISTS entity_relations (
    id SERIAL PRIMARY KEY,
    source_entity_id INT REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id INT REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL, -- ví dụ: 'belongs_to', 'created_by', 'subtopic'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_relation UNIQUE (source_entity_id, target_entity_id, relation_type)
);

-- 3. Bảng Assets: Lưu trữ các tài nguyên ảnh, video, prompt liên kết với thực thể
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    entity_id INT REFERENCES entities(id) ON DELETE SET NULL,
    asset_type VARCHAR(50) NOT NULL, -- 'image', 'video_broll', 'audio_music', 'voice_template'
    style_preset VARCHAR(100),       -- ví dụ: 'cinematic_painting', 'flat_vector'
    storage_path VARCHAR(512) NOT NULL, -- Đường dẫn cục bộ hoặc URL đám mây S3
    prompt_text TEXT,                -- Prompt được dùng để sinh ảnh/video nếu có
    ref_image_id INT REFERENCES assets(id), -- Tham chiếu ảnh gốc để đồng nhất nhân vật (IP-Adapter)
    meta_info JSONB,                 -- Lưu độ phân giải, định dạng, dung lượng, thời lượng
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Bảng Scripts: Quản lý kịch bản
CREATE TABLE IF NOT EXISTS scripts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    niche VARCHAR(100),              -- ví dụ: 'history', 'science', 'pets'
    raw_text TEXT,                   -- Kịch bản dạng chữ thô để review
    timeline_json JSONB NOT NULL,    -- Cấu trúc JSON timeline chi tiết từng phân cảnh
    status VARCHAR(50) DEFAULT 'draft', -- 'draft', 'verified', 'done'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. Bảng Channels: Quản lý các kênh xuất bản nội dung
CREATE TABLE IF NOT EXISTS channels (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,   -- 'youtube', 'tiktok', 'instagram'
    channel_url VARCHAR(512),
    meta_config JSONB,               -- Thông tin cấu hình OAuth, style mặc định
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. Bảng Videos: Quản lý video thành phẩm
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    script_id INT REFERENCES scripts(id) ON DELETE SET NULL,
    channel_id INT REFERENCES channels(id) ON DELETE SET NULL,
    filepath VARCHAR(512) NOT NULL,  -- Đường dẫn tới file MP4 thành phẩm
    platform_video_id VARCHAR(255),  -- ID video do YouTube/TikTok cấp khi upload
    status VARCHAR(50) DEFAULT 'queued', -- 'queued', 'rendering', 'rendered', 'published', 'failed'
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. Bảng Analytics Snapshots: Theo dõi hiệu suất video để phục vụ Self-Learning Loop
CREATE TABLE IF NOT EXISTS analytics_snapshots (
    id SERIAL PRIMARY KEY,
    video_id INT REFERENCES videos(id) ON DELETE CASCADE,
    views INT DEFAULT 0,
    ctr NUMERIC(5,2),                -- CTR (%) ví dụ: 5.40
    retention_rate NUMERIC(5,2),     -- Tỷ lệ giữ chân người xem (%) ví dụ: 45.20
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index hỗ trợ tìm kiếm nhanh thực thể
CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
CREATE INDEX IF NOT EXISTS idx_assets_entity_id ON assets(entity_id);
