from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import os
from app.database import init_db
from app.routers import loads, carriers, calls, dashboard

API_KEY = os.getenv("API_KEY", "happyrobot-fde-secret-2024")
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid or missing API key")
    return key

app = FastAPI(
    title="HappyRobot FDE — Inbound Carrier Sales API",
    description="AI-powered inbound carrier call automation for freight brokerages",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok", "service": "HappyRobot Carrier Sales API"}

# Protected routers
app.include_router(loads.router,     prefix="/api/loads",     tags=["Loads"],     dependencies=[Depends(get_api_key)])
app.include_router(carriers.router,  prefix="/api/carriers",  tags=["Carriers"],  dependencies=[Depends(get_api_key)])
app.include_router(calls.router,     prefix="/api/calls",     tags=["Calls"],     dependencies=[Depends(get_api_key)])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"], dependencies=[Depends(get_api_key)])

# Serve dashboard — mount static only if directory exists
if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/dashboard", include_in_schema=False)
def serve_dashboard():
    if os.path.exists("static/index.html"):
        return FileResponse("static/index.html")
    raise HTTPException(status_code=404, detail="Dashboard not built yet")

@app.on_event("startup")
def startup():
    init_db()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
