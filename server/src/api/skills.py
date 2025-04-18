import json

from fastapi import APIRouter

from services.OCRService import OCRService

router = APIRouter()

@router.get("/skills")
async def hello():
    ocr_service = OCRService()
    file_path = './data/Gerbylev.pdf'
    result, input_token, output_token = await ocr_service.process_file(file_path)

    parsed_result = json.loads(result)
    return parsed_result