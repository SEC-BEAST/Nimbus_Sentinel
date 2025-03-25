
from fastapi import FastAPI
from app.api import app as trace_router  # Import the APIRouter instance

# Initialize FastAPI app
app = FastAPI()

# Include the router from api.py
app.include_router(trace_router)

@app.get("/")
def root():
    return {"message": "Welcome to TraceX - Cloud Monitoring System"}
