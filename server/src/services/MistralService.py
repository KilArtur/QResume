import json

from mistralai import DocumentURLChunk, ImageURLChunk, TextChunk
from mistralai import Mistral
from mistralai.models import OCRResponse
from pathlib import Path

from config.config import CONFIG

class MistralService:

    def __init__(self):
        self.api_key_mistral = CONFIG.mistral.api_key_mistral
        self.model_mistral_chat = CONFIG.mistral.model_mistral_chat
        self.model_mistral_ocr = CONFIG.mistral.model_mistral_ocr
        self.client = Mistral(api_key=self.api_key_mistral)

    def process_pdf(self, pdf_file_path: str) -> str:
        pdf_file = Path(pdf_file_path)
        uploaded_file = self.client.files.upload(
            file={
                "file_name": pdf_file.stem,
                "content": pdf_file.read_bytes(),
            },
            purpose="ocr",
        )
        signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id,
                                                 expiry=1)

        pdf_response = self.client.ocr.process(document=DocumentURLChunk(document_url=signed_url.url),
                                          model=self.model_mistral_ocr,
                                          include_image_base64=False)

        data_ocr = self.__get_combined_markdown(pdf_response)

        return data_ocr

    def get_skills(self, data_ocr: str) -> json:
        chat_response = self.client.chat.complete(
            model="ministral-8b-latest",
            messages=[
                {
                    "role": "user",
                    "content": f"""This is the image's OCR in markdown:
        <BEGIN_IMAGE_OCR>
        {data_ocr}
        <END_IMAGE_OCR>

        Extract only the 8 technical hard skills explicitly mentioned in the text.  
        - **Exclude** any soft skills, languages (e.g., English, communication), general methodologies, or meta-skills.  
        - **Do not include** overlapping or nested skills (e.g., if PostgreSQL, MySQL is mentioned, include only SQL).  
        - **Select only programming languages, frameworks, libraries, tools, or platforms** that would be directly tested in a developer interview.

        Provide the output strictly as a JSON object in the following format:

        {{
            "skills": [
                "programming_language_or_technology_1",
                "programming_language_or_technology_2",
                ...
            ]
        }}

        Ensure the output is strictly in JSON format with no additional text or commentary.
        """
                },
            ],
            response_format={"type": "json_object"},
            temperature=0
        )

        response_dict = json.loads(chat_response.choices[0].message.content)
        json_string = json.dumps(response_dict, indent=4)

        decoded_json = json.loads(json_string)

        return json.dumps(decoded_json, indent=4, ensure_ascii=False)

    def __get_combined_markdown(self, ocr_response: OCRResponse) -> str:
        markdowns: list[str] = []
        for page in ocr_response.pages:
            image_data = {}
            for img in page.images:
                image_data[img.id] = img.image_base64
            markdowns.append(self.__replace_images_in_markdown(page.markdown, image_data))

        return "\n\n".join(markdowns)

    def __replace_images_in_markdown(self, markdown_str: str, images_dict: dict) -> str:
        for img_name, base64_str in images_dict.items():
            markdown_str = markdown_str.replace(f"![{img_name}]({img_name})", f"![{img_name}]({base64_str})")
        return markdown_str


if __name__ == "__main__":
    m = MistralService()
    data_cv = m.process_pdf('./data/Cherepov.pdf')
    result_json = m.get_skills(data_cv)
    print(result_json)