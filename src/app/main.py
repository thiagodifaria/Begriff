from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import settings
from app.controllers import auth_controller, twin_controller, analysis_controller, open_banking_controller
from domains.exceptions import UserNotFoundException, UserAlreadyExistsException, AnalysisGatewayError

from infra.persistence.database import engine, Base
from infra.persistence import models

app = FastAPI(title=settings.PROJECT_NAME)

@app.on_event("startup")
async def startup_event():
    """Cria todas as tabelas automaticamente no startup"""
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        
        table_names = list(Base.metadata.tables.keys())
        print(f"📋 Tables available: {table_names}")
        
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        
@app.exception_handler(UserNotFoundException)
async def user_not_found_exception_handler(request: Request, exc: UserNotFoundException):
    return JSONResponse(
        status_code=404,
        content={"message": exc.message},
    )

@app.exception_handler(UserAlreadyExistsException)
async def user_already_exists_exception_handler(request: Request, exc: UserAlreadyExistsException):
    return JSONResponse(
        status_code=400,
        content={"message": exc.message},
    )

@app.exception_handler(AnalysisGatewayError)
async def analysis_gateway_error_handler(request: Request, exc: AnalysisGatewayError):
    return JSONResponse(
        status_code=503,
        content={"message": exc.message},
    )

app.include_router(auth_controller.router, prefix="/api/v1", tags=["Authentication"])
app.include_router(twin_controller.router, prefix="/api/v1", tags=["Digital Twins"])
app.include_router(analysis_controller.router, prefix="/api/v1", tags=["Analysis"])
app.include_router(open_banking_controller.router, prefix="/api/v1", tags=["Open Banking"])

@app.get("/")
def read_root():
    return {"message": "Service is running"}