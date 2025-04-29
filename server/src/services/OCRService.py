import os
import json
import asyncio
import ocrmypdf
from typing import Type

import fitz
from pydantic import BaseModel
import contextlib
from openai import AsyncOpenAI

from config.config import CONFIG
from services.prompts import RECOGNIZE_FILE_PROMPT
from endpoints.models.recognize_response import CandidateProfile
from utils.loger import get_logger

log = get_logger("OCRService")

class OCRService:
    def __init__(self):
        self.openai = AsyncOpenAI(
            api_key=CONFIG.llm.api_key,
            base_url=CONFIG.llm.base_url
        )
        self.model = CONFIG.llm.model
        self.request_counter = 0
        self.total_input_token = 0
        self.total_output_token = 0

    async def process_file(self, file_path: str) -> tuple:
        text_for_prompt = self.get_str_info(file_path)
        model = self.model
        prompt = self.get_query(text_for_prompt)
        res = await self.fetch_completion(prompt=prompt, model=model, response_class=CandidateProfile)
        res = json.loads(res)
        return res, self.total_input_token, self.total_output_token

    def get_str_info(self, pdf_path) -> str:
        pdf_text = self.__extract_text_from_pdf(pdf_path)

        if pdf_text:
            return pdf_text

        else:
            input_pdf_path = pdf_path
            base, ext = os.path.splitext(input_pdf_path)
            output_pdf_path = f"{base}_CONVERT{ext}"

            pdf_text = self.__convert_scanned_pdf_to_text_pdf(pdf_path, output_pdf_path)

            if os.path.exists(output_pdf_path):
                os.remove(output_pdf_path)

            return pdf_text

    async def fetch_completion(self, prompt: str, model: str, args=None, response_class=Type[BaseModel] | None) -> str:
        self.request_counter += 1
        request_id = self.request_counter
        log.info(f"Текст к {self.model.rsplit('/', 1)[-1]} ({request_id}): {prompt}")

        counter = 0
        while True:
            try:
                res = await self.__fetch_completion(prompt, model, args or {}, response_class=response_class)
                return res
            except Exception as e:
                counter += 1
                if counter < 3:
                    log.warning(f"Ошибка при запросе к {self.model.rsplit('/', 1)[-1]}: {str(e)}")
                else:
                    raise e

    async def __fetch_completion(self, prompt: str, model: str, args, response_class=Type[BaseModel] | None) -> json:
        res = await self.openai.beta.chat.completions.parse(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0,
            top_p=0.5,
            response_format=response_class if response_class else {"type": "json_object"},
            **args
        )

        if res.usage:
            self.total_input_token += int(res.usage.prompt_tokens)
            self.total_output_token += int(res.usage.completion_tokens)
        else:
            log.info("Нет информации о токенах")

        return res.choices[0].message.content

    def get_query(self, text: str) -> str:
        return RECOGNIZE_FILE_PROMPT.render(data=text)

    def __extract_text_from_pdf(self, pdf_path: str) -> str | None:
        text = ""
        with fitz.open(pdf_path) as doc:
            for page in doc:
                text += page.get_text()
        return text

    def __convert_scanned_pdf_to_text_pdf(self, input_pdf_path: str, output_pdf_path: str) -> str:
        with open(os.devnull, 'w') as devnull:
            with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
                ocrmypdf.ocr(
                    input_pdf_path,
                    output_pdf_path,
                    language="rus+eng"
                )
        return self.__extract_text_from_pdf(output_pdf_path)


if __name__ == "__main__":
    file_path = 'data/CV_Kildiyarov_Artur.pdf'
    service = OCRService()

    answer, input_tokens, output_tokens = asyncio.run(service.process_file(file_path))

    log.info(type(answer))
    log.info(f'Ответ: {json.dumps(answer, indent=4, ensure_ascii=False)}')
    log.info(f'Входных токенов: {input_tokens}')
    log.info(f'Выходных токенов: {output_tokens}')