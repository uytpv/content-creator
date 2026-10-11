# Roadmap Production — CreatorOS

**Version:** 1.0  
**Status:** Production Draft  
**Last updated:** 2026-10-11  

## Milestone A — Foundation

**Goal:** Khởi tạo nền tảng local và kết nối YouTube Data API.

### Tasks

- [ ] Khởi tạo repo `creatoros`.
- [ ] Tạo cấu trúc `backend/`, `dashboard/`, `mcp/`, `docs/`.
- [ ] Setup Python venv, FastAPI, SQLAlchemy, SQLite.
- [ ] Setup Next.js dashboard.
- [ ] Tạo `.env.example`, `.gitignore`, README.
- [ ] Tạo Google Cloud project và bật YouTube Data API.
- [ ] Implement settings storage.
- [ ] Implement logger không ghi secret.
- [ ] Tạo `YouTubeDataSource` adapter.
- [ ] Kết nối và lấy metadata một kênh công khai.

### Acceptance criteria

- Backend chạy tại `http://localhost:8000`.
- Dashboard chạy tại `http://localhost:3000`.
- Hệ thống lưu được một kênh YouTube vào SQLite.
- Không có secret trong Git.

## Milestone B — Research Core

**Goal:** Xây nền tảng nghiên cứu kênh, video và ngách.

### Tasks

- [ ] CRUD niches.
- [ ] CRUD channel watchlist.
- [ ] Sync channel metadata.
- [ ] Sync video metadata.
- [ ] Lưu `channel_snapshots` và `video_snapshots`.
- [ ] Tính view growth.
- [ ] Tính views per day.
- [ ] Tính upload frequency.
- [ ] Tính median views của kênh.
- [ ] Xây trang Niches.
- [ ] Xây trang Channels.
- [ ] Xây trang Channel detail.

### Acceptance criteria

- Thêm được ít nhất 20 kênh.
- Sync được video metadata.
- Hiển thị được thay đổi view theo thời gian.
- Mọi sync job ghi log quota.

## Milestone C — Outlier & Idea Pipeline

**Goal:** Biến dữ liệu nghiên cứu thành pipeline nội dung.

### Tasks

- [ ] Outlier detector.
- [ ] Tính outlier ratio so với median kênh.
- [ ] Lưu `outlier_method_version`.
- [ ] CRUD ideas.
- [ ] Idea status workflow.
- [ ] AI idea generation.
- [ ] AI title generation.
- [ ] AI hook generation.
- [ ] AI outline generation.
- [ ] AI thumbnail brief generation.
- [ ] Trang Outliers.
- [ ] Trang Ideas.
- [ ] Trang Idea detail / Video brief.

### Acceptance criteria

- Hệ thống phát hiện được video có view velocity vượt baseline.
- Từ một kênh đối thủ, tạo được ít nhất 5 idea đã duyệt.
- Mỗi idea có title, hook, outline và thumbnail brief.
- Mọi output AI được đánh dấu là đề xuất.

## Milestone D — My Channel Performance

**Goal:** Kết nối và phân tích kênh YouTube riêng.

### Tasks

- [ ] OAuth 2.0 flow.
- [ ] Lưu refresh token encrypted.
- [ ] Đồng bộ video kênh riêng.
- [ ] Gọi YouTube Analytics API.
- [ ] Lưu views, estimatedMinutesWatched, averageViewDuration,
  averageViewPercentage, subscribersGained, subscribersLost.
- [ ] Tính baseline kênh.
- [ ] Phân loại `strong`, `normal`, `weak`, `anomaly`.
- [ ] AI đề xuất hành động.
- [ ] Trang My Channel Performance.

### Acceptance criteria

- Chỉ chủ kênh mới xem được analytics.
- Hệ thống hiển thị hiệu suất từng video.
- Hệ thống so sánh video với baseline kênh.
- AI đề xuất hành động cụ thể, có thể duyệt hoặc bỏ qua.

## Milestone E — MCP & Automation

**Goal:** Biến CreatorOS thành trợ lý AI local.

### Tasks

- [ ] Xây MCP server.
- [ ] Implement `search_niches`.
- [ ] Implement `get_channel_report`.
- [ ] Implement `find_outliers`.
- [ ] Implement `generate_ideas`.
- [ ] Implement `create_video_brief`.
- [ ] Implement `get_my_channel_performance`.
- [ ] Kết nối Cursor/Claude.
- [ ] APScheduler sync watchlist.
- [ ] Quota dashboard.

### Acceptance criteria

- AI client gọi được MCP tools.
- User có thể hỏi: “Phân tích kênh X và đề xuất 5 ý tưởng phù hợp với kênh của tôi.”
- Kết quả có trích dẫn dữ liệu và phiên bản heuristic.
- Scheduler chạy định kỳ không vượt quota.

## Definition of Done

Một milestone hoàn thành khi:

- Code có test cơ bản.
- Chạy được local.
- Không vi phạm hiến pháp dự án.
- Có log quota.
- Có UI hoặc API để kiểm chứng.
- Có tài liệu cập nhật.