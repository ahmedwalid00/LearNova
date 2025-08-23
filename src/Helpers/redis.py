from fastapi import Depends
from starlette.requests import Request


def get_redis(request: Request):
    """Dependency to retrieve the Redis client from app state."""
    return request.app.state.redis
