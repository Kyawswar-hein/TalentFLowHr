
from dotenv import load_dotenv
load_dotenv()
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.api.v1.endpoints import document, candidate, rag
from src.api.v1.endpoints import document, rag, analytics


# Import the main API router that maps to endpoints
from src.api.v1.router import api_router



app = FastAPI(
    title="Smart CV Screener & HR Matching Tool",
    description="Local Agentic RAG system for semantic resume screening and evaluation.",
    version="1.0.0"
)

# 1. Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Setup Jinja2 Templates Directory
# 'SRC_DIR' is D:\bilingual-rag-agent\src, so templates is in D:\bilingual-rag-agent\src\templates
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(SRC_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)


# 3. Jinja2 Rendered Frontend Page Routes
@app.get("/", response_class=HTMLResponse)
@app.get("/dashboard", response_class=HTMLResponse)
async def read_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/resumes", response_class=HTMLResponse)
async def read_resumes(request: Request):
    return templates.TemplateResponse("resumes.html", {"request": request})

@app.get("/candidates", response_class=HTMLResponse)
async def read_candidates(request: Request):
    return templates.TemplateResponse("candidates.html", {"request": request})

@app.get("/rag", response_class=HTMLResponse)
async def read_rag(request: Request):
    return templates.TemplateResponse("rag.html", {"request": request})

@app.get("/interview", response_class=HTMLResponse)
async def read_interview(request: Request):
    return templates.TemplateResponse("interview.html", {"request": request})


@app.get("/settings", response_class=HTMLResponse)
async def read_settings(request: Request):
    return templates.TemplateResponse("settings.html", {"request": request})

# 4. Core Backend API Routers
app.include_router(api_router, prefix="/api/v1")


# 5. Startup and Shutdown Hooks
@app.on_event("startup")
async def startup_event():
    print("Application startup: RAG Core and Vector pipeline initialized successfully.")

@app.on_event("shutdown")
async def shutdown_event():
    print("Application shutdown: Closing remaining database connections.")



app.include_router(document.router, prefix="/api/v1")
app.include_router(candidate.router, prefix="/api/v1")
app.include_router(rag.router, prefix="/api/v1")

app.include_router(analytics.router, prefix="/api/v1")
app.include_router(document.router, prefix="/api/v1")