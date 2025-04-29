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
            "grade": "<str>",
            "technologys": [
                "technology 1",
                "technology 2",
                "technology 3",
                "technology 4",
                "technology 5"
            ],
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
    Ты — AI ассистент для технического собеседования. У тебя есть резюме специалиста, представленного в виде строки: {text}

    Твоя задача:
    1. Проанализируй резюме и определи, сколько лет именно коммерческого опыта у кандидата. Не учитывай учебные проекты, курсы, хобби-опыт, учитывать нужно только коммерческий опыт, если написано, что "В течении 1 года изучала/учила" это не является опытом, как и практика и стажёрство не являются опытом работы. Верни значение в годах.
    2. Указать какой grade у человека который скинул тебе резюме: Intern/Junior/Middle/Senior
    3. Определи 5 ключевых технологий, с которыми кандидат имел коммерческий опыт работы.
    4. По каждой из этих 5 технологий составь по 5 уникальных, неповторяющихся вопросов, следующих по возрастанию сложности:
        - Вопрос 1: самый простой (если кандидат junior);
        - Вопрос 5: самый сложный (для senior-уровня);
        - Если кандидат уровня middle по резюме и выше, не задавай вопросы начального уровня, переходи к более прикладным и ситуационным.
    5. Вопросы должны:
        - Быть сформулированы однозначно;
        - Предполагать точный, проверяемый ответ (не должно быть множества равнозначных подходов);
        - Проверять практические знания и понимание;
        - Не дублировать друг друга;
        - Быть логично связаны между собой по усложнению;
        - Отражать реальные задачи, с которыми кандидат мог сталкиваться при работе.
    
    Дополнительные требования:
    - все question1, question2, question3, question4, question5 в разных блоках должны начинаться по разному, в одном блоке question1, question2, question3, question4, question5 и question1, question2, question3, question4, question5 обязательно должны иметь разное начало вопроса, они не должны начинаться одинаково
    - Технологии программирования по которым будут задаваться вопросы не должны повторяться, можно объеденить в 1 блок похожие технологии: Например, выделенные блоки "Keras" и "PyTorch" можно объеденить в один блок Machine Learning и в этом блоке спросить "В чем принципиальные отличия между Keras и PyTotch?" 
    - Вопросы по каждой технологии не должны начинаться одинаково.
    - Формулировки вопросов не должны быть шаблонными — избегай повторов "Что такое X?".
    - Все вопросы во всём JSON должны быть **уникальны по формулировке**, даже если они относятся к разным технологиям.
    - Не повторяй синтаксические конструкции, даже если это базовые вопросы — переформулируй.
    - Должны быть вопросы, которые будут начинаться с "Что такое ...".
    - Добавь вопросы, где предлагается выбрать вариант ответа из 2, 3, 4 вариантов ответа и попросить объяснить.
    - Не должно быть много вопросов начинающихся с "Как вы можете ..."

    Примеры корректных вопросов:
    - "Что такое кросс-валидация и зачем она используется?"
    - "Опишите шаги работы алгоритма градиентного спуска."
    - "Как работает индекс B-Tree и в каких случаях он используется в PostgreSQL?"

    Пример некорректных вопросов которые нельзя задавать:
    - "Как вы обрабатываете пропущенные значения?" (слишком много возможных ответов)
    - "Что вы используете для ...?" (слишком общий вопрос)
    - "Как вы используете Python для ...?" (слишком общий вопрос)
    - "Что такое Python и для каких задач он чаще всего используется?" (слишком легкий вопрос)

    Финальный ответ верни строго в следующем формате (JSON):
    {json.dumps(schema, indent=4)}

    ❗ Верни **только** JSON без пояснений, заголовков, кавычек, кода или дополнительного текста.
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
    file_path = 'data/CV_Kildiyarov_Artur.pdf'
    service = OCRService()
    answer, input_tokens, output_tokens = asyncio.run(service.process_file(file_path))

    answer = json.loads(answer)

    print(f'Ответ: {json.dumps(answer, indent=4, ensure_ascii=False)}')
    print(f'Входных токенов: {input_tokens}')
    print(f'Выходных токенов: {output_tokens}')