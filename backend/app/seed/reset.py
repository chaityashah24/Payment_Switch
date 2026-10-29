import sys
from app.config import settings
from app.database import Base, engine, SessionLocal
from app import models
from app.seed.seed_data import seed_database


def reset_development_demo():
    # Environment safety check
    if settings.ENVIRONMENT.lower() not in ["development", "demo", "test", "local"]:
        print(f"[ERROR] Reset command refused! Current ENVIRONMENT is '{settings.ENVIRONMENT}'. Reset is only permitted in development/demo environments.")
        sys.exit(1)

    print("[RESET] Resetting development database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database tables recreated.")

    seed_database()
    print("[SUCCESS] Database successfully reset and re-seeded with demo data!")
