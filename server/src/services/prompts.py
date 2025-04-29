import os

import yaml
from jinja2 import Template

prompt_file_path = os.path.join(os.path.dirname(__file__), 'prompts.yml')
with open(prompt_file_path, 'r', encoding='utf-8') as file:
    data = yaml.safe_load(file)

#RecognizeFile
RECOGNIZE_FILE_PROMPT = Template(data['recognize_file_prompt'])