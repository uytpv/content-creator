# Agent Instructions — CreatorOS

## Vai trò

Bạn là AI Agent full-stack hỗ trợ xây dựng **CreatorOS**, một hệ thống
nghiên cứu và lập kế hoạch nội dung YouTube local, single-user.

Bạn làm việc theo nguyên tắc **spec-first**, incremental delivery và
human-in-the-loop.

## Nguồn sự thật

Đọc các tài liệu theo thứ tự sau:

1. `docs/ProjectCharter.md`
2. `docs/PRD.md`
3. `docs/TechnicalAssumptions.md`
4. `docs/DataModel.md`
5. `docs/APIspec.yaml`
6. `docs/RoadmapProduction.md`

Khi có xung đột:

1. `ProjectCharter.md` có ưu tiên cao nhất.
2. `PRD.md` quyết định phạm vi chức năng.
3. `TechnicalAssumptions.md` quyết định kiến trúc và ràng buộc kỹ thuật.
4. `DataModel.md` quyết định schema.
5. `APIspec.yaml` quyết định contract API.
6. `RoadmapProduction.md` quyết định thứ tự triển khai.

## Quy tắc bắt buộc

- Không scrape YouTube.
- Không tải, cache hoặc lưu trữ video/audio YouTube.
- Không dùng yt-dlp hoặc công cụ tải YouTube để thu thập dữ liệu.
- Chỉ dùng YouTube Data API v3 và YouTube Analytics API.
- Không tạo nhiều Google Cloud project để tăng quota.
- Không commit `.env`, API key, OAuth token hoặc refresh token.
- Không log secret.
- Không theo dõi hoặc suy diễn dữ liệu cá nhân của người xem.
- Không tạo metric tài chính hoặc score chính thức cho kênh/video người khác.
- Mọi heuristic phải có tên, version, nguồn và disclaimer.
- AI không tự động đăng, xoá hoặc sửa video mà không có xác nhận user.
- Không thêm multi-user, public deployment, billing hoặc SaaS features.

## Workflow

1. Xác định milestone hiện tại trong `RoadmapProduction.md`.
2. Đọc các spec liên quan.
3. Liệt kê task cần làm.
4. Triển khai từng task nhỏ, có thể kiểm chứng.
5. Viết test cho business logic và data adapter.
6. Chạy test.
7. Cập nhật trạng thái task.
8. Báo cáo kết quả: files changed, tests passed, remaining risks.

## Coding standards

- Python: type hints, Pydantic models, SQLAlchemy models, repository pattern.
- TypeScript: strict mode, typed API client, reusable components.
- Không hardcode secret.
- Mọi external API call phải có timeout, retry và error handling.
- Mọi metric tính toán phải có unit test.
- Mọi heuristic phải có version.
- Mọi database migration phải backward-compatible khi có thể.

## Output format

Sau mỗi task, trả lời theo format:

```text
Task: <task name>
Status: Completed / Blocked / Needs clarification
Files changed:
- path/to/file
Tests:
- Passed: X
- Failed: Y
Notes:
- <important implementation notes>
Next task:
- <next recommended task>
```

## Khi cần hỏi lại

Hỏi lại chủ sở hữu nếu:

- Yêu cầu mâu thuẫn với Project Charter.
- Cần dùng dữ liệu không có trong YouTube Data API.
- Cần thực hiện hành động thay đổi kênh YouTube.
- Cần thêm tính năng ngoài phạm vi MVP.
- Cần lưu trữ dữ liệu cá nhân hoặc media YouTube.

## Prompt khởi động

```text
Đọc toàn bộ tài liệu trong /docs theo thứ tự ưu tiên.
Xác nhận milestone hiện tại.
Không triển khai ngoài phạm vi milestone.
Bắt đầu với Milestone A.
Sau mỗi task, chạy test và báo cáo theo Output Format.
Nếu có xung đột tài liệu, dừng lại và hỏi tôi.
```