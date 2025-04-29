from pydantic import BaseModel
from typing import List, Dict, Optional

class TechnologyQuestions(BaseModel):
    name_technology: str
    question1: str
    question2: str
    question3: str
    question4: str
    question5: str

class CandidateProfile(BaseModel):
    experience: float
    grade: str
    technologys: List[str]
    questions_by_technology: List[TechnologyQuestions]