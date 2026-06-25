# Migrate OSINT Tool to FastAPI + Next.js

This document outlines the architecture and steps required to upgrade this OSINT tool from a prototype Streamlit application to a premium, scalable, and responsive application using a decoupled backend (FastAPI) and frontend (Next.js).

## Proposed Architecture

### 1. Backend: FastAPI Integration
We will wrap the existing LangGraph logic in a lightweight asynchronous Python server.
- Setup `api/main.py` with FastAPI.
- Create a `/api/investigate` endpoint using Server-Sent Events (SSE). This replaces Streamlit's clunky polling loop and streams logs/progress to the client in real-time.
- Create `/api/reports` to list, fetch, and delete generated reports in the `reports/` folder.
- Ensure the backend properly handles the existing `.env` configuration.

### 2. Frontend: Next.js + Vanilla CSS
We will create a stunning, responsive, and highly interactive frontend. Per user preferences, we will avoid Tailwind and use pure, semantic Vanilla CSS to deliver a premium, tailored aesthetic.
- **Initialize Next.js**: Create a new `frontend/` directory with Next.js (App Router).
- **Design System**: Implement a high-end dark mode aesthetic using CSS variables (`colors`, `spacing`, `shadows`, `glassmorphism` effects, and micro-animations).
- **Investigate View**: A sleek search interface with the consent gate, target identifier, configuration toggles (Advanced vs Quick), and a beautiful streaming console for live logs.
- **Reports Dashboard**: A dedicated view to browse, read, and download previously generated Markdown/PDF/JSON reports with much better typography and readability than Streamlit offers.

### 3. Clean up and Update Tooling
- Update `docker-compose.yml` and `Dockerfile` to support building and serving both the FastAPI backend and Next.js frontend (or serving the built Next.js static files via FastAPI).
- Remove Streamlit dependencies and rewrite the UI tests in `tests/ui/` to test the new Next.js interface using Playwright.

## Open Design Decisions

1. **Deployment Strategy**: For simplicity and to keep it easily runnable for hobbyists, we can configure FastAPI to serve the exported static HTML/JS files of the Next.js app natively. This way, users still only need to run a single Python container/process instead of managing a separate Node.js server.
2. **Testing**: This migration will completely invalidate the Streamlit Playwright tests. We will need to rewrite the UI tests in `tests/ui/` to target the new Next.js DOM elements.
