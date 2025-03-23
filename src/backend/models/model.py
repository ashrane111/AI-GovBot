from pydantic import BaseModel
from typing import List, Optional, Any

class Query(BaseModel):
    role: str
    content: str

class MessagesList(BaseModel):
    messages: List[Query]

class Answer(BaseModel):
    content: str
    messages: List[Query]

class ResponseQuery(BaseModel):
    res: str
    answer: Answer