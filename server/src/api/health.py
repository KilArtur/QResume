from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
async def health():
    return {"status": "It's OK, nice work"}