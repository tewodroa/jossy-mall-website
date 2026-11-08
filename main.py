
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import json

# Initialize application
app = FastAPI(
    title="Jossy Mall",
    description="Official Jossy Mall Website",
    version="1.0.0"
)

# Project directories
BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
DATA_FILE = BASE_DIR / "items.json"

# Serve static files if the directory exists
if STATIC_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static"
    )


# Read mall information from JSON
def load_mall_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (FileNotFoundError, json.JSONDecodeError):
        raise HTTPException(
            status_code=500,
            detail="Mall data could not be loaded."
        )


# Homepage
@app.get("/")
def homepage():
    possible_files = [
        TEMPLATE_DIR / "items.html",
        BASE_DIR / "items.html"
    ]

    for html_file in possible_files:
        if html_file.is_file():
            return FileResponse(
                path=str(html_file),
                media_type="text/html"
            )

    raise HTTPException(
        status_code=404,
        detail="Homepage HTML file not found. Check items.html location."
    )


# Mall information API
@app.get("/api/mall")
def get_mall():
    return load_mall_data()


# Store directory API
@app.get("/api/stores")
def get_stores():
    data = load_mall_data()
    return data["stores"]


# Individual store information
@app.get("/api/stores/{store_id}")
def get_store(store_id: int):
    data = load_mall_data()

    for store in data["stores"]:
        if store["id"] == store_id:
            return store

    raise HTTPException(
        status_code=404,
        detail="Store not found"
    )


# Website health check
@app.get("/api/health")
def health():
    return {
        "status": "online",
        "website": "Jossy Mall"
    }
