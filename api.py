"""
api.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import asyncio

import storage
import planner
import weather_fetcher
import task_manager

storage.init_db()

app = FastAPI(
    title="Weather-Aware Smart Planner API",
    version="1.0.0",
    description="API for fetching weather forecasts and automatically rescheduling outdoor tasks."
)

class PlanRequest(BaseModel):
    location: str = "Ashta,IN"

class TaskCreate(BaseModel):
    title: str
    task_type: str = "outdoor"
    priority: str = "medium"
    scheduled_date: Optional[str] = None
    deadline: Optional[str] = None
    description: Optional[str] = ""

@app.get("/")
def read_root():
    return {"status": "online", "message": "Weather Planner API is operational"}

@app.get("/weather/{location}")
def get_weather(location: str):
    try:
        data = weather_fetcher.get_5day_forecast(location)
        return {"status": "success", "data": data}
    except weather_fetcher.WeatherFetchError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/planning/run")
def trigger_planning_cycle(payload: PlanRequest):
    try:
        summary = planner.run_planning_cycle(payload.location)
        return {
            "status": "success",
            "location": payload.location,
            "checked": summary["checked"],
            "rescheduled": summary["rescheduled"],
            "unresolved": summary["unresolved"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Planning cycle failed: {str(e)}")

@app.post("/tasks")
def add_task(task: TaskCreate):
    try:
        task_id = task_manager.create_task(
            title=task.title,
            task_type=task.task_type,
            description=task.description,
            priority=task.priority,
            deadline=task.deadline,
            scheduled_date=task.scheduled_date
        )
        return {"status": "success", "task_id": task_id}
    except task_manager.ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# Explicitly handle event loop for Python 3.14 on Windows
async def main():
    import uvicorn
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        loop="asyncio"
    )
    server = uvicorn.Server(config)
    server.install_signal_handlers = lambda: None
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Server stopped cleanly.")




# Bottom of api.py
async def main():
    import uvicorn
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=8000,
        log_level="info"
    )
    server = uvicorn.Server(config)
    
    # Start server and prevent premature loop shutdown
    await server.serve()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Server stopped cleanly.")