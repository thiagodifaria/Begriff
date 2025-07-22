from fastapi import FastAPI

from src.app.config import settings
from src.app.controllers import auth_controller, twin_controller, analysis_controller

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_controller.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(twin_controller.router, prefix="/api/v1", tags=["Digital Twins"])
app.include_router(analysis_controller.router, prefix="/api/v1", tags=["Analysis"])

@app.get("/")
def read_root():
    return {"message": "Service is running"}
