import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.db.init_db import init_db
from app.services.prediction_service import PredictionService
from app.services.retrieval_service import RetrievalService
from app.core.exceptions import NotFoundException, BusinessRuleViolationException, ValidationException

from app.api.routes.health import router as health_router
from app.api.routes.leads import router as leads_router
from app.api.routes.analyses import router as analyses_router
from app.api.routes.agent_runs import router as agent_runs_router
from app.api.routes.follow_ups import router as follow_ups_router
from app.api.routes.knowledge import router as knowledge_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.evaluation import router as evaluation_router
from app.api.routes.settings import router as settings_router

logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("nexusflow")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database tables and default configuration...")
    init_db()
    logger.info("Pre-loading machine learning models...")
    PredictionService.get_instance()
    logger.info("Initializing knowledge retrieval service and indexes...")
    RetrievalService.get_instance()
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} startup complete.")
    yield
    logger.info("Application shutdown.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Automated B2B Revenue Intelligence, Predictive Lead Qualification, and Agentic Sales Workflow Platform",
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS Configuration
origins = [
    settings.FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers with /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(leads_router, prefix="/api")
app.include_router(analyses_router, prefix="/api")
app.include_router(agent_runs_router, prefix="/api")
app.include_router(follow_ups_router, prefix="/api")
app.include_router(knowledge_router, prefix="/api")
app.include_router(analytics_router, prefix="/api")
app.include_router(evaluation_router, prefix="/api")
app.include_router(settings_router, prefix="/api")


# Global Exception Handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "Request validation failed", "errors": exc.errors()}
    )


@app.exception_handler(NotFoundException)
async def not_found_exception_handler(request: Request, exc: NotFoundException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(BusinessRuleViolationException)
async def business_rule_exception_handler(request: Request, exc: BusinessRuleViolationException):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled server error on {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred. Please consult backend logs."}
    )
