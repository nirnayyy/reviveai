from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.config import settings
from backend.app.database import init_db
from backend.app.api.cases import router as cases_router
from backend.app.api.webhooks import router as webhooks_router
from backend.app.api.simulation import router as simulation_router
from backend.app.api.audit import router as audit_router
from backend.app.api.evaluation import router as evaluation_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup safely
    try:
        await init_db()
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Database initialization warning on startup: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Adaptive AI Revenue Recovery Agent for Razorpay Merchants — Track 3: AI Revenue Recovery",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers
app.include_router(cases_router)
app.include_router(webhooks_router)
app.include_router(simulation_router)
app.include_router(audit_router)
app.include_router(evaluation_router)


@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "mode": "TEST_MODE" if settings.is_razorpay_configured else "SANDBOX_SIMULATION",
        "gemini_configured": settings.is_gemini_configured,
        "razorpay_configured": settings.is_razorpay_configured,
    }
