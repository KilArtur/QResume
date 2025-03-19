from fastapi import APIRouter
from server.src.api.welcome import router as welcome_router
from server.src.api.health import router as health_router
from server.src.api.hello import router as hello_router

main_router = APIRouter()

# main_router.include_router(welcome_router, tags=["Test"])
# main_router.include_router(health_router, tags=["Test"])
main_router.include_router(hello_router, tags=["Test"])

