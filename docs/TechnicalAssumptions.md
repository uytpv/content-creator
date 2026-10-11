# Technical Assumptions — CreatorOS

**Version:** 1.0  
**Status:** Draft  
**Last updated:** 2026-10-11  

## 1. Deployment model

- CreatorOS chạy hoàn toàn local.
- Backend và dashboard chạy trên cùng một máy.
- SQLite là database mặc định.
- Không yêu cầu Docker, nhưng Docker Compose là tuỳ chọn để tái lập môi trường.
- Không có public domain, CDN, cloud database hay managed hosting trong MVP.

## 2. Backend

### Stack

- Python 3.11+
- FastAPI
- Uvicorn
- SQLAlchemy 2.x
- SQLite
- APScheduler
- Pydantic
- httpx
- python-dotenv

### Kiến trúc module

```text
backend/
├─ app/
│  ├─ main.py
│  ├─ core/
│  │  ├─ config.py
│  │  ├─ database.py
│  │  ├─ security.py
│  │  └─ logging.py
│  ├─ api/
│  │  ├─ routes_settings.py
│  │  ├─ routes_channels.py
│  │  ├─ routes_videos.py
│  │  ├─ routes_niches.py
│  │  ├─ routes_ideas.py
│  │  └─ routes_analytics.py
│  ├─ modules/
│  │  ├─ youtube/
│  │  ├─ niches/
│  │  ├─ ideas/
│  │  ├─ analytics/
│  │  └─ ai/
│  └─ workers/
│     ├─ sync_jobs.py
│     └─ scheduler.py
├─ tests/
└─ requirements.txt
```

## 3. YouTube integration

### APIs sử dụng

| API | Mục đích |
|---|---|
| YouTube Data API v3 | Tìm kiếm, channel, video, playlist, comment metadata |
| YouTube Analytics API | Dữ liệu hiệu suất kênh/video của chủ sở hữu |
| OAuth 2.0 | Uỷ quyền truy cập kênh riêng |

### Endpoint ưu tiên

| Endpoint | Mục đích | Lưu ý quota |
|---|---|---|
| `channels.list` | Lấy channel metadata | Dùng cho watchlist |
| `videos.list` | Lấy/cập nhật video metadata | Ưu tiên khi đã có video ID |
| `search.list` | Tìm kênh/video từ keyword | Dùng hạn chế, có bucket riêng |
| `playlistItems.list` | Lấy video trong playlist | Dùng khi cần |
| `reports.query` | YouTube Analytics | Chỉ dùng cho kênh riêng |

### Quota policy

- Một Google Cloud project duy nhất.
- Mỗi job sync phải ghi `quota_units_used`.
- Không chạy sync song song quá 2 job.
- Retry tối đa 3 lần với exponential backoff.
- Nếu gặp quota error, dừng job và lên lịch retry vào ngày sau.
- Không dùng nhiều project để tăng quota.

## 4. Data retention

### Được phép lưu

- Channel metadata.
- Video metadata.
- Thumbnail URL.
- Numeric metrics công khai.
- Snapshot lịch sử metric.
- Kết quả phân tích heuristic.
- Brief và idea do user tạo.
- Log sync job không chứa secret.

### Không được phép lưu

- File video YouTube.
- File audio YouTube.
- Bản sao transcript phục vụ phát lại hoặc download.
- OAuth token trong database plaintext.
- Dữ liệu cá nhân không cần thiết.
- Dữ liệu cá nhân hoá người xem.

## 5. AI architecture

### AI responsibilities

- Phân tích dữ liệu nghiên cứu.
- Sinh idea.
- Sinh title, hook, outline, thumbnail brief.
- Tổng hợp báo cáo hiệu suất.
- Đề xuất hành động.

### AI boundaries

- Không tự động đăng video.
- Không tự động xoá hoặc sửa video.
- Không truy cập dữ liệu kênh người khác ngoài dữ liệu công khai.
- Không sao chép nguyên văn nội dung có bản quyền.
- Mọi output phải lưu `model`, `prompt_version`, `input_refs`, `generated_at`.

### MCP

MCP server expose tool cho AI client. MCP cho phép server công bố tool qua
`tools/list` và client gọi tool qua `tools/call`. [43][48]

Tools MVP:

```text
search_niches
get_channel_report
find_outliers
generate_ideas
create_video_brief
get_my_channel_performance
```

## 6. Dashboard

### Stack

- Next.js 14+
- React
- TypeScript
- Tailwind CSS
- TanStack Query
- Recharts

### Screens MVP

1. Dashboard.
2. Niches.
3. Channels.
4. Channel detail.
5. Outliers.
6. Ideas.
7. Idea detail / Video brief.
8. My channel performance.
9. Settings.

## 7. Security

- `.env` không commit.
- `.env.example` chỉ chứa tên biến.
- OAuth refresh token lưu encrypted tại local disk.
- API key không được ghi vào log.
- Database backup phải được mã hoá nếu chứa token hoặc dữ liệu nhạy cảm.
- CORS chỉ cho phép `http://localhost:3000`.

## 8. Testing strategy

| Loại | Phạm vi |
|---|---|
| Unit test | Metric calculation, heuristic, repository |
| Integration test | YouTube API adapter với mocked response |
| E2E test | Thêm kênh, sync video, tạo idea, tạo brief |
| Quota test | Đảm bảo job log đúng endpoint và units |
| Security test | Không leak secret, không commit `.env` |

## 9. Technical decisions

| Quyết định | Lựa chọn | Lý do |
|---|---|---|
| Database | SQLite | Đơn giản, local-first, backup dễ |
| Backend | Python + FastAPI | Phù hợp data/AI workflow |
| Scheduler | APScheduler | Nhẹ, tích hợp trực tiếp Python |
| Dashboard | Next.js | UI linh hoạt và mở rộng tốt |
| AI integration | MCP | Chuẩn hoá tool access cho AI client |
| Media storage | Không lưu | Tuân thủ chính sách YouTube |