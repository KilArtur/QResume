import os
import tempfile
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, HTTPException
from utils.loger import get_logger

from services.OCRService import OCRService
from endpoints.models.recognize_response import CandidateProfile

router = APIRouter()
log = get_logger("skills_endpoint")

@router.post("/skills", response_model=CandidateProfile)
async def process_resume(file: UploadFile = File(...)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            content = await file.read()
            temp_file.write(content)
        
        log.info(f"Файл {file.filename} успешно загружен и сохранен во временный файл")
        
        ocr_service = OCRService()
        result, input_token, output_token = await ocr_service.process_file(temp_file_path)
        
        log.info(f"Файл успешно обработан. Использовано токенов: вход={input_token}, выход={output_token}")
        log.info(f"Результат обработки: {result}")
        
        os.unlink(temp_file_path)
        
        return result
    except Exception as e:
        log.error(f"Ошибка при обработке файла: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Ошибка при обработке файла: {str(e)}")
