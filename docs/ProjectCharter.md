# Project Charter — CreatorOS

**Project codename:** CreatorOS  
**Version:** 1.0  
**Status:** Approved  
**Owner:** Single user — project owner  
**Created:** 2026-10-11  
**Last updated:** 2026-10-11  

## 1. Mục đích

CreatorOS là một hệ thống nội dung cá nhân chạy local, giúp chủ sở hữu:

- Nghiên cứu ngách YouTube.
- Theo dõi kênh và video đối thủ.
- Phát hiện video tăng trưởng bất thường.
- Sinh và quản lý ý tưởng video.
- Lập kế hoạch tiêu đề, hook, outline và thumbnail.
- Theo dõi hiệu suất kênh riêng.
- Đưa ra quyết định nội dung dựa trên dữ liệu.

Hệ thống kết hợp tư duy của Nexlev và vidIQ:

| Nguồn cảm hứng | Vấn đề giải quyết |
|---|---|
| Nexlev | “Nên làm ngách, chủ đề hoặc mô hình kênh nào?” |
| vidIQ | “Video/kênh hiện tại cần tối ưu gì để tăng hiệu quả?” |
| CreatorOS | “Với kênh, gu và mục tiêu của riêng tôi, bước tiếp theo là gì?” |

## 2. Phạm vi

### Trong phạm vi MVP

- Quản lý ngách và kênh đối thủ.
- Đồng bộ metadata video/kênh qua YouTube Data API.
- Tính toán chỉ số tăng trưởng cơ bản.
- Phát hiện video outlier.
- Quản lý pipeline ý tưởng video.
- Sinh nội dung planning bằng AI.
- Kết nối và phân tích kênh YouTube riêng của chủ sở hữu.
- Dashboard local.
- Job scheduler và quota logging.

### Ngoài phạm vi MVP

- Public deployment.
- Multi-user.
- Billing hoặc subscription.
- Scraping YouTube.
- Tải, cache hoặc phát lại video/audio YouTube.
- Tự động đăng video.
- RPM/CPM predictor trình bày như số liệu chính thức.
- Hệ thống chấm điểm kênh người khác như một chỉ số chính thức.

## 3. Hiến pháp dự án

Các quy tắc sau là bắt buộc. Mọi PRD, API, agent instruction và tính năng phải tuân theo.

### 3.1 Local-first

- Hệ thống chạy trên máy local.
- Không yêu cầu public server, domain hay hosting.
- Không có multi-user, registration, sharing hay remote access trong MVP.
- Database và file cấu hình nằm trên máy chủ sở hữu.

### 3.2 Dữ liệu YouTube hợp pháp

- Chỉ dùng YouTube Data API v3 làm nguồn dữ liệu YouTube chính.
- Dùng API key cho public data.
- Dùng OAuth 2.0 cho dữ liệu riêng tư của kênh chủ sở hữu.
- Không scrape YouTube web/app.
- Không dùng yt-dlp hoặc công cụ tương tự để thu thập nội dung.
- Không lưu trữ, cache hay phát lại video/audio YouTube.
- Chỉ lưu metadata và metric cần thiết cho phân tích.

### 3.3 Quota-first

- Một Google Cloud project duy nhất.
- Có rate limiter, exponential backoff và job scheduler.
- Ưu tiên `videos.list` với video ID đã biết thay vì lạm dụng `search.list`.
- Không tạo nhiều project để tăng quota.
- Mọi job sync phải log endpoint, quota units, trạng thái và lỗi.

### 3.4 Quyền riêng tư

- Không suy diễn danh tính, vị trí, lịch sử xem, demographic, tôn giáo,
  sức khoẻ, xu hướng chính trị hay thuộc tính nhạy cảm của người xem.
- Không thu thập dữ liệu cá nhân không cần thiết.
- YouTube Analytics chỉ dùng cho kênh mà chủ sở hữu hệ thống là chủ kênh.

### 3.5 Metric trung thực

- Không trình bày ước tính doanh thu, RPM, CPM, watch time, unique reach,
  demographic hay “ad safety” của kênh/video người khác như số liệu YouTube.
- Không tạo score tùy chế để xếp hạng hoặc thay thế YouTube Analytics.
- Mọi heuristic nội bộ phải có tên, phiên bản, nguồn và mô tả công thức.
- Ví dụ: `internal_opportunity_score_v1`, `research_heuristic`, 
  `not_official_youtube_metric`.

### 3.6 AI human-in-the-loop

- AI phân tích, đề xuất và sinh tài liệu planning.
- AI không tự động đăng, xoá hoặc thay đổi video mà không có xác nhận.
- AI không sao chép nguyên văn nội dung có bản quyền.
- Mọi output AI phải ghi rõ là gợi ý, không phải cam kết kết quả.

### 3.7 Bảo mật

- Không commit API key, OAuth token, refresh token vào Git.
- Dùng `.env` local.
- Không ghi token hoặc secret vào log.
- Có chức năng export và xoá dữ liệu cá nhân.

## 4. Mục tiêu thành công

MVP thành công khi chủ sở hữu có thể:

1. Thêm và đồng bộ ít nhất 20 kênh đối thủ.
2. Xem lịch sử thay đổi view và tốc độ tăng trưởng video.
3. Phát hiện video có view velocity vượt baseline kênh.
4. Tạo và duyệt ít nhất 50 idea.
5. Sinh title, hook, outline và thumbnail brief.
6. Kết nối kênh riêng và xem hiệu suất cơ bản.
7. Chạy toàn bộ hệ thống local mà không cần public infrastructure.

## 5. Rủi ro chính

| Rủi ro | Biện pháp |
|---|---|
| Hết quota YouTube API | Rate limiter, sync chọn lọc, cache, ưu tiên video ID |
| YouTube thay đổi chính sách | Tách `YouTubeDataSource`, chỉ dùng official API |
| AI đề xuất kém | Human approval, feedback loop, học từ video hiệu quả của chủ kênh |
| Scope creep | Chỉ triển khai theo milestone, không thêm public/multi-user |
| Secret lộ | `.env`, `.gitignore`, không log token |