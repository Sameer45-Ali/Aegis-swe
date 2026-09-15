"""
FastAPI Server and Real-Time WebSocket Streaming API for Aegis-SWE.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from aegis.benchmarks.benchmark_suite import BenchmarkSuiteRunner
from aegis.benchmarks.fixtures import BENCHMARK_TASKS
from aegis.config import settings
from aegis.core.mcts.tree_search import MCTSSearchEngine

app = FastAPI(
    title="Aegis-SWE Autonomous Agent API",
    version="0.1.0",
    description="Backend API and WebSocket streaming server for Aegis-SWE."
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ActiveWebSocketsManager:
    """Manages connected WebSocket clients for real-time MCTS tree streaming."""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event: Dict[str, Any]):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(event))
            except Exception:
                pass


ws_manager = ActiveWebSocketsManager()


class SolveRequest(BaseModel):
    repo_path: str
    issue_description: str
    max_iterations: int = 10


class SolveResponse(BaseModel):
    status: str
    solution_found: bool
    best_node: Optional[Dict[str, Any]] = None
    git_diff: Optional[str] = None


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "provider": settings.llm_provider,
        "sandbox_mode": settings.sandbox_mode
    }


@app.get("/api/benchmarks")
async def get_benchmarks():
    return [
        {
            "task_id": t.task_id,
            "repository": t.repository,
            "issue_title": t.issue_title,
            "issue_description": t.issue_description
        }
        for t in BENCHMARK_TASKS
    ]


@app.post("/api/solve", response_model=SolveResponse)
async def solve_issue(request: SolveRequest):
    loop = asyncio.get_running_loop()

    def handle_mcts_event(event: Dict[str, Any]):
        # Schedule broadcast on running event loop
        asyncio.run_coroutine_threadsafe(ws_manager.broadcast(event), loop)

    engine = MCTSSearchEngine(
        repo_path=request.repo_path,
        issue_description=request.issue_description,
        on_node_event=handle_mcts_event
    )

    solution = await engine.run_search(max_iterations=request.max_iterations)

    return SolveResponse(
        status="completed",
        solution_found=solution is not None,
        best_node=solution.to_dict() if solution else None,
        git_diff=solution.git_diff if solution else None
    )


@app.post("/api/benchmarks/run")
async def run_benchmark_suite():
    runner = BenchmarkSuiteRunner()
    results = await runner.run_all()
    return {"status": "completed", "results": results}


@app.websocket("/ws/live")
async def websocket_live_stream(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Keep-alive
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
