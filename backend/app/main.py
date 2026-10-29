from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import api_v1_router
from app.core.correlation import CorrelationIdMiddleware
from app.core.exceptions import SwitchException, switch_exception_handler, generic_exception_handler
from app.database import Base, engine
from app import models

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "ACADEMIC SIMULATION: Educational platform for demonstrating payment switch operations, "
        "merchant acquiring, double-entry ledger accounting, bank authorization/capture, settlement, "
        "and 3-way reconciliation for LNTFINTECH. This platform does NOT connect to real banks, "
        "NPCI, card networks, or real payment gateways."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.env = settings.ENVIRONMENT

# Create tables on startup if not present
Base.metadata.create_all(bind=engine)

# Correlation ID Middleware
app.add_middleware(CorrelationIdMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Correlation-ID"],
)

# Exception handlers
app.add_exception_handler(SwitchException, switch_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Include API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)


@app.get("/")
def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "status": "OPERATIONAL",
        "simulation_disclaimer": "FOR EDUCATIONAL PURPOSES ONLY. NO REAL FINANCIAL TRANSACTIONS OCCUR.",
        "docs_url": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "HEALTHY", "service": "payment-switch-backend"}
