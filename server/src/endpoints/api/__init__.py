from fastapi import APIRouter
from endpoints.api.welcome import router as welcome_router
from endpoints.api.health import router as health_router
from endpoints.api.hello import router as hello_router
from endpoints.api.skills import router as skills_router

main_router = APIRouter()

main_router.include_router(welcome_router, tags=["Test"])
main_router.include_router(health_router, tags=["Test"])
main_router.include_router(hello_router, tags=["Test"])
main_router.include_router(skills_router, tags=['Peoples skills'])
