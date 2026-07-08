# Project Context & Agent Guidelines

## 1. Visual & Layout Standards (UI/UX)
- **Theme**: Neutral darkmode tech theme (Antigravity IDE style). Use charcoal gray (`#121316`), deep slate black (`#0a0b0d`), steel gray boundaries (`#2a2c31`), and dark textareas (`#0d0e11`).
- **Color Constraint**: **Do NOT use purple or blue-purple slate tones.** Focus colors should be high-tech neon cyan (`#00f2fe`) and teal (`#14b8a6`).
- **Layout**:
  - The right column panel (`.sticky-right-panel`) is sticky (`position: sticky; top: 102px`) and has an independent inner scrollbar (`.pane-content-wrapper` with `overflow-y: auto`).
  - The top Titlebar and Menu bar are also sticky to preserve the IDE container frame during page scroll.
  - The PostgreSQL Database Report is integrated into the right panel as a tab (`db_report.sql` / `tab-db-report`) and linked to the **"Database"** option in the mock toolbar.

## 2. Dynamic Features
- The `workspace_setup.log` tab functions as a live system log. Log events using `addSystemLog(message, type)` when users query ideas, click cards, or change settings.
- Switching tabs automatically hides/shows relevant wrappers (`#status-waiting`, `#status-loading`, `#editor-wrapper`, `#video-wrapper`, `#db-report-wrapper`) and syncs active highlights on the mock menu bar.

## 3. Next Session Focus: Local LLM Integration
- The primary task of the next session is to **connect the AI Agent system with the local GLM 5.2 model** for video script timeline compilation.
- Ensure the connection is fully offline/local (using standard compatible API endpoints such as Ollama or LocalAI), zero-cost, and optimized for high-performance generation.
