# CreatorOS — Personal YouTube Content OS

CreatorOS là hệ thống nghiên cứu và lập kế hoạch nội dung YouTube chạy local,
single-user, phục vụ riêng cho một creator độc lập.

Hệ thống kết hợp:

- **Market intelligence**: tìm ngách, theo dõi đối thủ, phát hiện video outlier.
- **Content planning**: sinh ý tưởng, tiêu đề, hook, outline và thumbnail brief.
- **Performance intelligence**: theo dõi hiệu suất kênh/video của chính bạn.

## Nguyên tắc cốt lõi

- Local-first: chạy trên máy cá nhân, không public.
- Single-user: chỉ phục vụ chủ sở hữu hệ thống.
- YouTube Data API first: không scrape YouTube.
- No media storage: không tải, cache hay phát lại video/audio YouTube.
- Human-in-the-loop: AI đề xuất, người dùng phê duyệt.
- Traceable metrics: mọi con số suy luận phải có nguồn và phiên bản công thức.

## Tech stack mặc định

- Python 3.11+
- FastAPI
- SQLite
- SQLAlchemy
- APScheduler
- Next.js + React + TypeScript
- MCP server
- YouTube Data API v3
- YouTube Analytics API

## Khởi chạy nhanh

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Dashboard:

```bash
cd dashboard
npm install
npm run dev
```

## Cấu trúc tài liệu

```text
docs/
├─ ProjectCharter.md
├─ PRD.md
├─ TechnicalAssumptions.md
├─ DataModel.md
├─ APIspec.yaml
├─ RoadmapProduction.md
└─ AgentInstructions.md
```

## Trạng thái

| Hạng mục | Trạng thái |
|---|---|
| Project Charter | Approved |
| PRD | Draft |
| Technical design | Draft |
| Implementation | Not started |