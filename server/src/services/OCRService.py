import os
import json
import asyncio
import ocrmypdf

import fitz
import contextlib
from openai import AsyncOpenAI

from config.config import CONFIG


class OCRService:
    def __init__(self):
        self.openai = AsyncOpenAI(
            api_key=CONFIG.gpt.api_key,
            base_url=CONFIG.gpt.base_url
        )
        self.model = CONFIG.gpt.model
        self.request_counter = 0
        self.total_input_token = 0
        self.total_output_token = 0

    async def fetch_completion(self, prompt: str, model: str, args=None) -> str:
        self.request_counter += 1
        request_id = self.request_counter
        print(f"Текст к GPT ({request_id}): {prompt}")

        counter = 0
        while True:
            try:
                res = await self.__fetch_completion(prompt, model, args or {})
                return res
            except Exception as e:
                counter += 1
                if counter < 3:
                    print(f"Ошибка при запросе к GPT: {str(e)}")
                else:
                    raise e

    async def __fetch_completion(self, prompt: str, model: str, args) -> json:
        res = await self.openai.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0,
            top_p=0.5,
            stream=False,
            # response_format={"type": "json_object"},
            **args
        )

        if res.usage:
            self.total_input_token += int(res.usage.prompt_tokens)
            self.total_output_token += int(res.usage.completion_tokens)
        else:
            print("Нет информации о токенах")

        return res.choices[0].message.content

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

    async def process_file(self, file_path: str) -> tuple:
        text = self.get_str_info(file_path)
        model = self.model
        prompt = self.get_query(text)
        res = await self.fetch_completion(prompt, model)
        # result_json = json.loads(res)
        return res, self.total_input_token, self.total_output_token

    def get_query(self, text: str) -> str:

        schema = {
            "experience": "<float>",
            "technologys": ["technology 1", "technology 2", "technology 3", "technology 4", "technology 5"],
            "technology 1": [{
                "question1": "<str>",
                "question2": "<str>",
                "question3": "<str>",
                "question4": "<str>",
                "question5": "<str>"
            }],
            "technology 2": [{
                "question1": "<str>",
                "question2": "<str>",
                "question3": "<str>",
                "question4": "<str>",
                "question5": "<str>"
            }]
        }

        query = f"""
        Ты ассистент для проведения собеседований IT специалистов, у тебя есть информация по резюме специалиста с которым нужно провести собеседование.
        Воn текст резюме специалиста в формате строки: {text} 
        
        ВАЖНО: 
        - Считать только релевантный опыт для резюме, если коммерческого опыта нет, то вернуть в ответе 0, опыт нужно вернуть в годах 
        - Задавать нужно неповторяющиеся вопросы
        - Вопросы должны отображать то, чем должен заниматься специалист 
        - Вопросы должны быть по возрастанию сложности 
        - Каждый следующий вопрос должен быть продолжением другого, кроме первого соответственно
        - Если у человека опыт соответствует уже полноценному специалисту уровня middle (2-3 года) то не нужно спрашивать самые базовые вещи, спроси про то как необходимо и в каких случаях использовать ту или иную технологию 
        - Вопросы должны быть такие, чтобы по ним можно было однозначно поставить оценку по ответу специалиста не должно быть вопросов с размытым ответом или несколькими вариантами ответа, например: "Как вы обрабатываете пропущенные значения в данных?" есть много вариантов, с помощью которых правильно ответить на вопрос 
        - Вопросы не должны быть размытые, вопросы должны иметь точный ответ, желательно в вопросе нужно попросить специалиста разъяснить ответ 
            
        Тебе необходимо выделить по резюме опыт работы и 5 основных технологий, с помощью которых ты сможешь проверить компетенции человека в соответствии с его опытом.
        финальный ответ нужно вернуть в следующем формате: 
        
        СХЕМА:
        {json.dumps(schema, indent=4)}
        
        В ответ верни только результирующий JSON который в точности соответствует предоставленной СХЕМЕ,  ничего кроме этого возвращать не надо не надо начинать ответ с "```json" верни только json 
        """
        return query

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
    file_path = './data/Gerbylev.pdf'
    service = OCRService()
    answer, input_tokens, output_tokens = asyncio.run(service.process_file(file_path))

    answer = json.loads(answer)

    print(f'Ответ: {json.dumps(answer, indent=4, ensure_ascii=False)}')
    print(f'Входных токенов: {input_tokens}')
    print(f'Выходных токенов: {output_tokens}')