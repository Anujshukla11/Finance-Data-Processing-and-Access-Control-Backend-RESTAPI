from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from app.database.setup import initialize_db
from app.routers import records, dashboard

# Initialize the main FastAPI app
app = FastAPI(
    title="Finance Dashboard API",
    description="Backend API for managing financial records with role-based access control.",
    version="1.0.0"
)

app.include_router(records.router)
app.include_router(dashboard.router)

# This will automatically run when the app starts
@app.on_event("startup")
def startup_event():
    initialize_db()

@app.get("/")
def read_root():
    return RedirectResponse(url="/docs")
