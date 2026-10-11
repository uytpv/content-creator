# Product Requirements Document — CreatorOS

**Version:** 1.0  
**Status:** Draft  
**Last updated:** 2026-10-11  
**Related docs:** ProjectCharter.md, TechnicalAssumptions.md, DataModel.md, RoadmapProduction.md

## 1. Product overview

CreatorOS là một ứng dụng local, single-user, giúp creator độc lập vận hành
vòng đời nội dung YouTube:

```text
Research → Idea → Plan → Produce → Publish → Analyze → Improve
```

Hệ thống không phải là công cụ tăng view tự động. Nó là công cụ hỗ trợ ra
quyết định: chọn ngách, nghiên cứu đối thủ, tạo ý tưởng và đánh giá hiệu suất.

## 2. Target user

**Primary user:** Chủ sở hữu hệ thống — một creator độc lập.

User cần một hệ thống có thể trả lời:

- Ngách nào đáng nghiên cứu tiếp?
- Kênh nào đang làm tốt mô hình tương tự?
- Video nào đang tăng view nhanh bất thường?
- Tôi nên làm 5 video nào trong tuần này?
- Tiêu đề và thumbnail nào phù hợp với kênh của tôi?
- Video nào của tôi đang hiệu quả và nên làm phần tiếp theo?
- Chủ đề nào nên ngừng mở rộng?

## 3. Product principles

1. **Local-first:** dữ liệu và quyền kiểm soát nằm trên máy cá nhân.
2. **Single-user:** không có user management hay chia sẻ.
3. **Data traceability:** mọi metric đều truy vết được nguồn và công thức.
4. **Human-in-the-loop:** AI đề xuất, người dùng quyết định.
5. **No scraping:** chỉ dùng YouTube Data API và YouTube Analytics API.
6. **Incremental delivery:** mỗi milestone phải chạy được và kiểm chứng được.

## 4. Functional requirements

### FR-01 — Settings & Connections

Hệ thống phải cho phép người dùng:

- Lưu YouTube API key.
- Kết nối kênh YouTube riêng bằng OAuth.
- Xem trạng thái kết nối.
- Cấu hình tần suất sync.
- Xem quota usage gần đây.

**Priority:** P0

### FR-02 — Niche management

Hệ thống phải cho phép:

- Tạo ngách mới.
- Gắn từ khoá vào ngách.
- Ghi chú cơ hội, rủi ro và giả thuyết.
- Đánh dấu trạng thái: `active`, `watching`, `paused`, `archived`.

**Priority:** P0

### FR-03 — Channel watchlist

Hệ thống phải cho phép:

- Thêm kênh YouTube bằng URL, handle hoặc channel ID.
- Gán kênh vào một hoặc nhiều ngách.
- Đặt trạng thái theo dõi.
- Ghi chú lý do theo dõi.
- Xem lần sync gần nhất.

**Priority:** P0

### FR-04 — Video metadata sync

Hệ thống phải:

- Đồng bộ metadata video công khai: title, description, thumbnail URL,
  published date, duration, view count, like count, comment count, tags.
- Lưu snapshot theo thời gian.
- Hỗ trợ sync theo kênh hoặc theo video ID.
- Ghi log quota tiêu tốn.

**Priority:** P0

### FR-05 — Growth metrics

Hệ thống phải tính:

- View growth giữa hai lần sync.
- Views per day.
- Upload frequency.
- Median views của kênh.
- View-to-subscriber ratio.
- Outlier ratio.

**Priority:** P0

### FR-06 — Outlier detection

Hệ thống phải:

- So sánh view velocity của video với baseline kênh.
- Đánh dấu video là `outlier_candidate`.
- Hiển thị hệ số so với median.
- Lưu phiên bản heuristic và thời điểm tính.

**Priority:** P0

### FR-07 — Idea pipeline

Hệ thống phải hỗ trợ pipeline:

```text
Idea → Research → Planned → Production → Published → Review → Archived
```

Người dùng có thể:

- Tạo idea thủ công.
- Tạo idea từ nghiên cứu ngách/đối thủ.
- Chỉnh sửa, duyệt hoặc từ chối idea.
- Gán priority và nguồn gốc.

**Priority:** P0

### FR-08 — AI content studio

Với một idea, hệ thống phải có thể sinh:

- 5–10 title candidates.
- Hook 15 giây đầu.
- Outline theo cấu trúc retention.
- Thumbnail brief.
- Mô tả video draft.
- Tags đề xuất.

Người dùng phải có thể chỉnh sửa và lưu phiên bản cuối.

**Priority:** P0

### FR-09 — My channel analytics

Hệ thống phải:

- Kết nối kênh riêng bằng OAuth.
- Đồng bộ danh sách video của kênh.
- Truy vấn YouTube Analytics: views, estimatedMinutesWatched,
  averageViewDuration, averageViewPercentage, subscribersGained, subscribersLost.
- So sánh video với baseline kênh.

**Priority:** P1

### FR-10 — Dashboard

Dashboard phải hiển thị:

- Tổng quan ngách đang theo dõi.
- Kênh đối thủ và lần sync gần nhất.
- Video outlier mới.
- Pipeline idea.
- Hiệu suất video kênh riêng.

**Priority:** P0

### FR-11 — MCP integration

Hệ thống phải expose MCP tools để AI client có thể:

- Tìm ngách từ từ khoá.
- Lấy báo cáo kênh.
- Tìm video outlier.
- Sinh ý tưởng.
- Tạo video brief.
- Truy vấn hiệu suất kênh riêng.

**Priority:** P1

## 5. Non-functional requirements

| ID | Yêu cầu |
|---|---|
| NFR-01 | Ứng dụng chạy local, không cần public server |
| NFR-02 | Một user duy nhất |
| NFR-03 | API key và token không được commit vào Git |
| NFR-04 | Mọi sync job phải log quota |
| NFR-05 | Hệ thống phải hoạt động khi mất mạng, chỉ hạn chế sync |
| NFR-06 | Dashboard phản hồi dưới 500 ms với dữ liệu local thông thường |
| NFR-07 | Database có thể backup bằng file SQLite |
| NFR-08 | Không lưu trữ video/audio YouTube |
| NFR-09 | Mọi output AI phải được đánh dấu là đề xuất |

## 6. User flows

### 6.1 Research flow

```text
User nhập keyword hoặc channel URL
→ Hệ thống gọi YouTube Data API
→ Lưu channel/video metadata
→ Tính growth metrics
→ Hiển thị Niche Radar
→ User lưu ngách hoặc thêm kênh vào watchlist
```

### 6.2 Idea generation flow

```text
User chọn niche hoặc source channel
→ AI tạo idea candidates
→ User duyệt / chỉnh sửa / từ chối
→ Idea chuyển sang Planned
→ AI tạo video brief
→ User duyệt brief
→ Idea chuyển sang Production
```

### 6.3 Performance review flow

```text
User kết nối kênh riêng
→ Hệ thống sync video + analytics
→ So sánh với baseline
→ Hệ thống phân loại video hiệu quả / yếu / bất thường
→ AI đề xuất hành động
→ User phê duyệt hoặc bỏ qua
```

## 7. MVP acceptance criteria

MVP hoàn thành khi:

- [ ] Chạy local thành công.
- [ ] Có một Google Cloud project duy nhất.
- [ ] Thêm được ít nhất 20 kênh đối thủ.
- [ ] Sync metadata video thành công.
- [ ] Lưu lịch sử sync và thay đổi view.
- [ ] Phát hiện được video outlier.
- [ ] Tạo và quản lý ít nhất 50 idea.
- [ ] Sinh được title, hook, outline và thumbnail brief.
- [ ] Kết nối kênh riêng và hiển thị analytics cơ bản.
- [ ] Không scrape YouTube.
- [ ] Không lưu media YouTube.
- [ ] Không commit secret.
- [ ] Mọi heuristic có version và nguồn rõ ràng.

## 8. Out of scope

- Multi-user.
- Public deployment.
- Subscription/billing.
- Scraping.
- Tải hoặc phát video offline.
- Tự động đăng video.
- Dự báo doanh thu kênh người khác.
- Hệ thống chấm điểm chính thức kênh/video người khác.