from fastapi import Depends
from starlette.requests import Request


def get_redis_client(request: Request):
    """Dependency to retrieve the Redis client from app state."""
    return request.app.state.redis
