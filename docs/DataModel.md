# Data Model — CreatorOS

**Version:** 1.0  
**Status:** Draft  
**Last updated:** 2026-10-11  

## 1. Nguyên tắc

- Mọi bảng có `created_at` và `updated_at`.
- Mọi dữ liệu YouTube phải lưu `source`.
- Mọi metric suy luận phải lưu `method_version`.
- Không lưu video/audio YouTube.
- Không lưu secret trong database plaintext.

## 2. ERD sơ bộ

```text
Niche 1---N Channel
Niche 1---N Idea
Channel 1---N Video
Channel 1---N ChannelSnapshot
Video 1---N VideoSnapshot
Idea 1---1 VideoBrief
SyncJob N---1 Channel / Video
```

## 3. Tables

### `niches`

| Field | Type | Description |
|---|---|---|
| id | UUID PK | ID ngách |
| name | TEXT | Tên ngách |
| description | TEXT | Mô tả |
| keywords | JSON | Danh sách từ khoá |
| status | ENUM | `active`, `watching`, `paused`, `archived` |
| opportunity_notes | TEXT | Ghi chú cơ hội |
| risk_notes | TEXT | Ghi chú rủi ro |
| created_at | DATETIME | Thời điểm tạo |
| updated_at | DATETIME | Thời điểm cập nhật |

### `channels`

| Field | Type | Description |
|---|---|---|
| id | UUID PK | ID nội bộ |
| youtube_channel_id | TEXT UNIQUE | Channel ID YouTube |
| title | TEXT | Tên kênh |
| handle | TEXT | Handle |
| description | TEXT | Mô tả |
| thumbnail_url | TEXT | URL thumbnail |
| country | TEXT | Quốc gia |
| subscriber_count | INTEGER | Subscriber hiện tại |
| video_count | INTEGER | Số video |
| view_count | INTEGER | Tổng view |
| niche_id | UUID FK | Ngách chính |
| watch_status | ENUM | `active`, `paused`, `archived` |
| watch_reason | TEXT | Lý do theo dõi |
| first_seen_at | DATETIME | Lần đầu lưu |
| last_synced_at | DATETIME | Lần sync gần nhất |

### `channel_snapshots`

| Field | Type | Description |
|---|---|---|
| id | UUID PK | ID snapshot |
| channel_id | UUID FK | Kênh |
| subscriber_count | INTEGER | Subscriber |
| view_count | INTEGER | Tổng view |
| video_count | INTEGER | Số video |
| captured_at | DATETIME | Thời điểm chụp |

### `videos`

| Field | Type | Description |
|---|---|---|
| id | UUID PK | ID nội bộ |
| youtube_video_id | TEXT UNIQUE | Video ID YouTube |
| channel_id | UUID FK | Kênh |
| title | TEXT | Tiêu đề |
| description | TEXT | Mô tả |
| thumbnail_url | TEXT | URL thumbnail |
| published_at | DATETIME | Ngày đăng |
| duration_seconds | INTEGER | Thời lượng |
| view_count | INTEGER | View hiện tại |
| like_count | INTEGER | Like |
| comment_count | INTEGER | Comment |
| tags | JSON | Tags |
| category_id | TEXT | Category |
| is_outlier_candidate | BOOLEAN | Có phải outlier |
| outlier_score | FLOAT | Điểm heuristic nội bộ |
| outlier_method_version | TEXT | Phiên bản công thức |
| first_seen_at | DATETIME | Lần đầu lưu |
| last_synced_at | DATETIME | Lần sync gần nhất |

### `video_snapshots`

| Field | Type | Description |
|---|---|---|
| id | UUID PK | ID snapshot |
| video_id | UUID FK | Video |
| view_count | INTEGER | View |
| like_count | INTEGER | Like |
| comment_count | INTEGER | Comment |
| captured_at | DATETIME | Thời điểm chụp |

### `niches`

Xem bảng `niches` ở trên.

### `ideas`

| Field | Type | Description |
|---|---|---|
| id | UUID PK | ID idea |
| niche_id | UUID FK | Ngách |
| source_channel_id | UUID FK nullable | Kênh nguồn |
| source_video_id | UUID FK nullable | Video nguồn |
| title_candidate | TEXT | Tiêu đề dự kiến |
| angle | TEXT | Góc tiếp cận |
| target_audience | TEXT | Đối tượng |
| status | ENUM | `idea`, `research`, `planned`, `production`, `published`, `review`, `archived` |
| priority | INTEGER | 1–5 |
| ai_generated | BOOLEAN | AI tạo hay user tạo |
| user_approved | BOOLEAN | Đã duyệt |
| created_at | DATETIME | Thời điểm tạo |
| updated_at | DATETIME | Thời điểm cập nhật |

### `video_briefs`

| Field | Type | Description |
|---|---|---|
| id | UUID PK | ID brief |
| idea_id | UUID FK | Idea |
| final_title | TEXT | Tiêu đề cuối |
| hook | TEXT | Hook mở đầu |
| outline | JSON | Outline |
| thumbnail_brief | TEXT | Brief thumbnail |
| description_draft | TEXT | Mô tả draft |
| tags | JSON | Tags |
| production_notes | TEXT | Ghi chú sản xuất |
| status | ENUM | `draft`, `approved`, `production`, `published` |
| created_at | DATETIME | Thời điểm tạo |
| updated_at | DATETIME | Thời điểm cập nhật |

### `my_channel_videos`

| Field | Type | Description |
|---|---|---|
| id | UUID PK | ID nội bộ |
| youtube_video_id | TEXT UNIQUE | Video ID |
| title | TEXT | Tiêu đề |
| published_at | DATETIME | Ngày đăng |
| views | INTEGER | Views |
| estimated_minutes_watched | INTEGER | Watch time |
| average_view_duration_seconds | INTEGER | Average view duration |
| average_view_percentage | FLOAT | Average view percentage |
| subscribers_gained | INTEGER | Subscriber gained |
| subscribers_lost | INTEGER | Subscriber lost |
| baseline_median_views | INTEGER | Baseline kênh |
| performance_label | ENUM | `strong`, `normal`, `weak`, `anomaly` |
| performance_method_version | TEXT | Phiên bản heuristic |
| synced_at | DATETIME | Lần sync gần nhất |

### `sync_jobs`

| Field | Type | Description |
|---|---|---|
| id | UUID PK | ID job |
| job_type | ENUM | `channel_sync`, `video_sync`, `analytics_sync` |
| target_type | ENUM | `channel`, `video`, `niche` |
| target_id | UUID | ID đối tượng |
| endpoint | TEXT | Endpoint đã gọi |
| quota_units_used | INTEGER | Units tiêu tốn |
| status | ENUM | `success`, `failed`, `rate_limited`, `quota_exceeded` |
| started_at | DATETIME | Bắt đầu |
| finished_at | DATETIME | Kết thúc |
| error_message | TEXT | Lỗi |

## 4. Heuristic versioning

Mọi score phải có bản ghi:

```json
{
  "metric": "internal_opportunity_score",
  "version": "v1",
  "source": "youtube_data_api",
  "formula": "view_velocity / channel_median_view_velocity",
  "computed_at": "2026-10-11T18:00:00Z",
  "disclaimer": "Internal research heuristic. Not an official YouTube metric."
}
```