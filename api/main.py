import json
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from graph.workflow import create_workflow

app = FastAPI(title="Digital Footprint Investigator API")

# Add CORS for local Next.js development (port 3000 -> 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InvestigateRequest(BaseModel):
    target: str
    config: dict


def get_saved_reports() -> list[Path]:
    reports_dir = Path("reports").resolve()
    if not reports_dir.exists():
        return []
    files = sorted(reports_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files


@app.post("/api/investigate")
async def investigate(req: InvestigateRequest):
    target = req.target
    config = req.config

    if not target or not target.strip():
        raise HTTPException(status_code=400, detail="Target is required")

    async def event_generator():
        workflow = create_workflow()
        inputs = {"target": target, "config": config}
        thread_id = f"api_{uuid.uuid4()}"
        thread_config = {"configurable": {"thread_id": thread_id}}

        yield {
            "event": "message",
            "data": json.dumps({"type": "info", "content": f"Starting investigation for '{target}'..."}),
        }

        try:
            # Note: We stream state updates. In a production app you might stream token-by-token or logs.
            final_report = None
            async for event in workflow.astream(inputs, thread_config):
                node_name = list(event.keys())[0]
                if node_name == "report_node" and "report" in event[node_name]:
                    final_report = event[node_name]["report"]

                yield {
                    "event": "message",
                    "data": json.dumps({"type": "update", "content": f"Completed analysis phase: {node_name}"}),
                }

            yield {
                "event": "message",
                "data": json.dumps({"type": "done", "content": "Investigation complete!", "report": final_report}),
            }
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"type": "error", "content": str(e)})}

    return EventSourceResponse(event_generator())


@app.get("/api/reports")
async def list_reports():
    reports = get_saved_reports()
    return [{"name": p.name, "size": p.stat().st_size, "created_at": p.stat().st_mtime} for p in reports]


@app.get("/api/reports/{filename}")
async def get_report(filename: str):
    reports_dir = Path("reports").resolve()
    target_path = (reports_dir / filename).resolve()
    if not str(target_path).startswith(str(reports_dir)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(target_path)


@app.delete("/api/reports/{filename}")
async def delete_report(filename: str):
    reports_dir = Path("reports").resolve()
    target_path = (reports_dir / filename).resolve()
    if not str(target_path).startswith(str(reports_dir)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    if not target_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    base_path = target_path.with_suffix("")
    for ext in [".md", ".json", ".html", ".pdf"]:
        p = base_path.with_suffix(ext)
        if p.exists():
            p.unlink()

    return {"message": "Deleted successfully"}


@app.delete("/api/reports")
async def delete_all_reports():
    reports = get_saved_reports()
    for rf in reports:
        base_path = rf.with_suffix("")
        for ext in [".md", ".json", ".html", ".pdf"]:
            p = base_path.with_suffix(ext)
            if p.exists():
                p.unlink()
    return {"message": "All reports deleted"}


# Mount frontend last so it doesn't intercept /api routes
frontend_dir = Path("frontend/out").resolve()
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
else:

    @app.get("/")
    async def root():
        return {"message": "Frontend build not found. Run 'npm run build' in the frontend directory."}
