import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.app.config import settings
from src.app.controllers import analysis_controller, auth_controller, open_banking_controller, report_controller, twin_controller
from src.app.middleware.security import SecurityHeadersMiddleware
from src.domains.identity.services.auth_service import ensure_default_admin_user
from src.domains.exceptions import AnalysisGatewayError, UserAlreadyExistsException, UserNotFoundException
from src.infra.persistence import models
from src.infra.persistence.database import Base, SessionLocal, engine

app = FastAPI(title=settings.PROJECT_NAME)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    try:
        if settings.DATABASE_URL.startswith("sqlite:///./"):
            sqlite_path = settings.DATABASE_URL.replace("sqlite:///./", "", 1)
            sqlite_dir = os.path.dirname(sqlite_path)
            if sqlite_dir:
                os.makedirs(sqlite_dir, exist_ok=True)
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        try:
            ensure_default_admin_user(db)
        finally:
            db.close()
    except Exception as e:
        print(f"Error creating database tables: {e}")


@app.exception_handler(UserNotFoundException)
async def user_not_found_exception_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(status_code=404, content={"message": exc.message})


@app.exception_handler(UserAlreadyExistsException)
async def user_already_exists_exception_handler(request: Request, exc: UserAlreadyExistsException):
    return JSONResponse(status_code=400, content={"message": exc.message})


@app.exception_handler(AnalysisGatewayError)
async def analysis_gateway_error_handler(request: Request, exc: AnalysisGatewayError):
    return JSONResponse(status_code=503, content={"message": exc.message})


app.include_router(auth_controller.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(twin_controller.router, prefix="/api/v1", tags=["Digital Twins"])
app.include_router(analysis_controller.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(open_banking_controller.router, prefix="/api/v1", tags=["Open Banking"])
app.include_router(report_controller.router, prefix="/api/v1", tags=["UI"])


@app.get("/", tags=["Status"])
def read_root():
    return {"message": "Service is running"}
