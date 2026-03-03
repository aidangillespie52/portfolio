from fastapi import APIRouter
from app.api import commands, health

api_router = APIRouter()
api_router.include_router(commands.router, tags=["commands"])
api_router.include_router(health.router, tags=["health"])