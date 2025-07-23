from typing import Optional, List

from pydantic import BaseModel

class FormSessionResponse(BaseModel):
    session_id: str
    filename: str
    total_fields: int
    status: str


class FormFieldResponse(BaseModel):
    field_name: str
    field_type: str
    is_filled: bool
    value: Optional[str] = None


class QuestionResponse(BaseModel):
    question: str
    field_name: Optional[str]
    field_type: Optional[str]
    is_complete: bool


class AnswerRequest(BaseModel):
    field_name: str
    answer: str


class FormCompletionResponse(BaseModel):
    session_id: str
    download_url: str
    filled_fields: int
    total_fields: int