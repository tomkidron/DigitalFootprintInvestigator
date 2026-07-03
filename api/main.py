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

    valid_files = []
    for p in reports_dir.glob("*.md"):
        # Resolve both and check if it's strictly within reports_dir
        if str(p.resolve()).startswith(str(reports_dir)):
            valid_files.append(p)

    files = sorted(valid_files, key=lambda p: p.stat().st_mtime, reverse=True)
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
            final_report = None
            final_filename = None
            async for event in workflow.astream_events(inputs, thread_config, version="v2"):
                kind = event["event"]
                name = event.get("name", "")

                if kind == "on_custom_event" and name == "investigation_log":
                    msg = event["data"].get("message", "")
                    yield {
                        "event": "message",
                        "data": json.dumps({"type": "update", "content": msg}),
                    }
                elif kind == "on_chain_start":
                    if name in ["google_search", "social_search", "analysis", "advanced_analysis", "report"]:
                        yield {
                            "event": "message",
                            "data": json.dumps(
                                {"type": "update", "content": f"Starting phase: {name.replace('_', ' ')}..."}
                            ),
                        }
                elif kind == "on_chain_end":
                    if name in ["google_search", "social_search", "analysis", "advanced_analysis", "report"]:
                        yield {
                            "event": "message",
                            "data": json.dumps(
                                {"type": "update", "content": f"Completed phase: {name.replace('_', ' ')}"}
                            ),
                        }
                    elif name == "LangGraph":
                        output = event["data"].get("output", {})
                        if output and isinstance(output, dict) and "report" in output:
                            final_report = output["report"]
                            final_filename = output.get("report_filename")

            yield {
                "event": "message",
                "data": json.dumps(
                    {
                        "type": "done",
                        "content": "Investigation complete!",
                        "report": final_report,
                        "filename": final_filename,
                    }
                ),
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
