from enum import StrEnum


class DocumentStatus(StrEnum):
    QUEUED = 'queued'
    PROCESSING = 'processing'
    INDEXED = 'indexed'
    FAILED = 'failed'
    DELETED = 'deleted'


class QueryStatus(StrEnum):
    ANSWERED = 'answered'
    NEEDS_CLARIFICATION = 'needs_clarification'
    NOT_FOUND = 'not_found'
    FAILED = 'failed'


class MessageRole(StrEnum):
    USER = 'user'
    ASSISTANT = 'assistant'
