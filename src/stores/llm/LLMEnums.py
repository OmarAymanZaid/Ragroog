from enum import Enum

class LLMEnums(Enum):
    OPENAI = "OPENAI"
    COHERE = "COHERE"

class DocumentTypeEnum(Enum):
    DOCUMENT = "document"
    QUERY = "query"