from fastapi import APIRouter

from services.MistralService import MistralService

router = APIRouter()

@router.get("/skills")
async def hello():
    mistral_service = MistralService()
    result = mistral_service.get_skills(mistral_service.process_pdf(('./data/Cherepov.pdf')))
    return result