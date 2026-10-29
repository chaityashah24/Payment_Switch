from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.merchants import router as merchants_router
from app.api.v1.accounts import router as accounts_router
from app.api.v1.payments import router as payments_router
from app.api.v1.refunds import router as refunds_router
from app.api.v1.settlements import router as settlements_router
from app.api.v1.reconciliation import router as reconciliation_router
from app.api.v1.risk import router as risk_router
from app.api.v1.scenarios import router as scenarios_router
from app.api.v1.admin import router as admin_router
from app.api.v1.reports import router as reports_router

api_v1_router = APIRouter()
api_v1_router.include_router(auth_router)
api_v1_router.include_router(merchants_router)
api_v1_router.include_router(accounts_router)
api_v1_router.include_router(payments_router)
api_v1_router.include_router(refunds_router)
api_v1_router.include_router(settlements_router)
api_v1_router.include_router(reconciliation_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(scenarios_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(reports_router)
