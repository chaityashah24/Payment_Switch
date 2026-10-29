import sys
import argparse
from app.seed.seed_data import seed_database
from app.seed.reset import reset_development_demo
from app.worker.engine import WorkerEngine
from app.database import SessionLocal
from app.services.ledger_service import verify_ledger_invariants


def main():
    parser = argparse.ArgumentParser(description="Payment Switch CLI Tooling")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    subparsers.add_parser("seed", help="Seed initial development demo data")
    subparsers.add_parser("reset-demo", help="Safely reset and re-seed the development demo database")
    subparsers.add_parser("worker", help="Start background worker process")
    subparsers.add_parser("verify-ledger", help="Verify double-entry ledger balance invariants")

    args = parser.parse_args()

    if args.command == "seed":
        seed_database()
    elif args.command == "reset-demo":
        reset_development_demo()
    elif args.command == "worker":
        worker = WorkerEngine()
        worker.start()
    elif args.command == "verify-ledger":
        db = SessionLocal()
        try:
            res = verify_ledger_invariants(db)
            print("Ledger Integrity Status:", res)
        finally:
            db.close()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
