from pydantic import BaseModel
from typing import List, Optional, Any

class Query(BaseModel):
    messages: List[Any]