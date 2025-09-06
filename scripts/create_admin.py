import argparse
import asyncio
import sys
from typing import Optional
from pathlib import Path

# Make project root importable so `import src.*` works when running this script directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.Helpers.config import get_settings
from src.Models.repositories.user_repository import AdminRepository
from src.Models.services.id_generation_service import IDGenerationService
from src.Api.utils import PasswordHandler


async def create_admin(name: str, email: str, password: str, admin_type: str = "ADMIN", unique_id_override: Optional[str] = None) -> int:
    """
    Create a new admin using existing repositories/services without modifying app code.

    - Generates a unique admin ID (e.g., ADMIN001)
    - Hashes the password using the existing PasswordHandler (bcrypt)
    - Inserts the admin via AdminRepository and commits the transaction

    Returns process exit code (0 on success, non-zero on error)
    """
    settings = get_settings()

    dsn = (
        f"postgresql+asyncpg://{settings.POSTGRES_USERNAME}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_MAIN_DATABASE}"
    )

    engine = create_async_engine(dsn)
    SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with SessionLocal() as session:
            repo = AdminRepository(session)
            id_service = IDGenerationService(session)

            email_l = email.strip().lower()

            # Ensure email is not already used
            existing = await repo.get_by_email(email_l)
            if existing is not None:
                print(f"Error: An admin with email '{email_l}' already exists (unique_id={existing.unique_id}).", file=sys.stderr)
                return 2

            # Use provided unique_id if given; otherwise generate (ADMIN### or SUPER###)
            if unique_id_override and unique_id_override.strip():
                unique_id = unique_id_override.strip()
            else:
                unique_id = await id_service.generate_admin_id(admin_type.strip().upper() or "ADMIN")

            # Hash password with PasswordHandler (same as used in auth)
            pwd_hash = PasswordHandler.hash_password(password)

            # Create admin
            admin = await repo.create(name=name.strip(), email=email_l, password_hash=pwd_hash, unique_id=unique_id)
            await session.commit()

            print("Admin created successfully:\n"
                  f"  name       : {admin.name}\n"
                  f"  email      : {admin.email}\n"
                  f"  unique_id  : {admin.unique_id}")
            return 0
    except Exception as e:
        print(f"Failed to create admin: {e}", file=sys.stderr)
        return 1
    finally:
        try:
            await engine.dispose()
        except Exception:
            pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create a new admin in the database (no code changes)")
    parser.add_argument("--name", required=True, help="Admin full name")
    parser.add_argument("--email", required=True, help="Admin email (must be unique)")
    parser.add_argument("--password", required=True, help="Admin password (will be hashed)")
    parser.add_argument("--type", dest="admin_type", default="ADMIN", choices=["ADMIN", "SUPER"], help="Admin ID prefix (default: ADMIN)")
    parser.add_argument("--unique-id", dest="unique_id", default=None, help="Explicit unique_id to use (skips auto-generation)")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    exit_code = asyncio.run(create_admin(args.name, args.email, args.password, args.admin_type, args.unique_id))
    sys.exit(exit_code)
