from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.app.config import settings
from src.app.controllers import auth_controller, twin_controller, analysis_controller, open_banking_controller
from src.domains.exceptions import UserNotFoundException, UserAlreadyExistsException, AnalysisGatewayError

app = FastAPI(title=settings.PROJECT_NAME)

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
