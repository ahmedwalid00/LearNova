from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Request
from typing import AsyncGenerator

async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get a database session for a single request.
    
    This ensures proper transaction management where the entire request
    is treated as a single atomic transaction.
    """
    session_factory = request.app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise