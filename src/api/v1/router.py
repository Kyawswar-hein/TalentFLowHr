from fastapi import APIRouter
# 1. Correct the import to pull all three from the endpoints folder
from src.api.v1.endpoints import agent, chat, document
from src.api.v1.endpoints import interview

api_router = APIRouter()

# 2. Include routers cleanly without duplicating the prefixes/tags
api_router.include_router(document.router)
api_router.include_router(agent.router, prefix="/agent", tags=["agent"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(interview.router)