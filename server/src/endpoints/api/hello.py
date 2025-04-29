from fastapi import APIRouter

router = APIRouter()

@router.get("/hello/{name}")
async def hello(name: str):
    return {"message": f"Hello {name}"}