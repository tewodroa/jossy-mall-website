
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Literal
from datetime import datetime, timezone
from threading import Lock
import json
import os

# --------------------------------
# 1. Application configuration
# --------------------------------

app = FastAPI(
    title="Student Task Manager",
    description="An advanced task management API",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "items.json"
HTML_FILE = BASE_DIR / "templates" / "items.html"

file_lock = Lock()


# --------------------------------
# 2. JSON database functions
# --------------------------------

def load_data():
    with file_lock:
        if not DATA_FILE.exists():
            return {"tasks": [], "next_id": 1}

        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            raise HTTPException(
                status_code=500,
                detail="The JSON database is invalid."
            )


def save_data(data):
    with file_lock:
        temp_file = DATA_FILE.with_suffix(".tmp")

        temp_file.write_text(
            json.dumps(data, indent=4),
            encoding="utf-8"
        )

        os.replace(temp_file, DATA_FILE)


def get_current_time():
    return datetime.now(timezone.utc).isoformat()


# --------------------------------
# 3. Task data models
# --------------------------------

class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    priority: Literal["Low", "Medium", "High"] = "Medium"


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    priority: Literal["Low", "Medium", "High"] | None = None
    completed: bool | None = None


# --------------------------------
# 4. Homepage
# --------------------------------

@app.get("/")
def homepage():
    if not HTML_FILE.exists():
        raise HTTPException(404, "HTML file not found")

    return FileResponse(HTML_FILE)


# --------------------------------
# 5. Retrieve all tasks
# --------------------------------

@app.get("/api/tasks")
def get_tasks(
    search: str = Query(default="", max_length=100),
    status: Literal["all", "pending", "completed"] = "all"
):
    data = load_data()
    tasks = data["tasks"]

    if search:
        tasks = [
            task for task in tasks
            if search.lower() in task["title"].lower()
            or search.lower() in task["description"].lower()
        ]

    if status == "pending":
        tasks = [task for task in tasks if not task["completed"]]

    elif status == "completed":
        tasks = [task for task in tasks if task["completed"]]

    return tasks


# --------------------------------
# 6. Create a new task
# --------------------------------

@app.post("/api/tasks", status_code=201)
def create_task(task: TaskCreate):
    data = load_data()

    new_task = {
        "id": data["next_id"],
        "title": task.title.strip(),
        "description": task.description.strip(),
        "priority": task.priority,
        "completed": False,
        "created_at": get_current_time()
    }

    if not new_task["title"]:
        raise HTTPException(400, "Task title cannot be empty")

    data["tasks"].append(new_task)
    data["next_id"] += 1

    save_data(data)

    return new_task


# --------------------------------
# 7. Update an existing task
# --------------------------------

@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, updates: TaskUpdate):
    data = load_data()

    for task in data["tasks"]:
        if task["id"] == task_id:

            changes = updates.model_dump(exclude_unset=True)

            for key, value in changes.items():
                if key == "title" and value is not None:
                    value = value.strip()
                    if not value:
                        raise HTTPException(
                            400, "Task title cannot be empty"
                        )

                if value is not None:
                    task[key] = value

            save_data(data)
            return task

    raise HTTPException(404, "Task not found")


# --------------------------------
# 8. Delete a task
# --------------------------------

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    data = load_data()

    original_count = len(data["tasks"])

    data["tasks"] = [
        task for task in data["tasks"]
        if task["id"] != task_id
    ]

    if len(data["tasks"]) == original_count:
        raise HTTPException(404, "Task not found")

    save_data(data)

    return {"message": "Task deleted successfully"}


# --------------------------------
# 9. Task statistics
# --------------------------------

@app.get("/api/statistics")
def get_statistics():
    data = load_data()
    tasks = data["tasks"]

    total = len(tasks)
    completed = sum(task["completed"] for task in tasks)
    pending = total - completed

    percentage = round(
        (completed / total) * 100, 1
    ) if total else 0

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
        "completion_percentage": percentage
    }
