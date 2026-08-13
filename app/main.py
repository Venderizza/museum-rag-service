from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.api.v1.router import api_router
from app.config.settings import get_settings
from app.domain.errors import (
    DocumentAlreadyDeletedError,
    DocumentAlreadyExistsError,
    DocumentDeletedError,
    DocumentNotFoundError,
    DomainError,
    EmbeddingProviderError,
    LLMProviderError,
    VectorStoreError,
)
from app.infrastructure.logging.setup import setup_logging

settings = get_settings()
setup_logging(settings.log_level)

app = FastAPI(title='Museum RAG Service', version='0.1.0')
app.include_router(api_router)


ERROR_STATUS_MAP = {
    DocumentAlreadyExistsError: 409,
    DocumentNotFoundError: 404,
    DocumentAlreadyDeletedError: 409,
    DocumentDeletedError: 409,
    EmbeddingProviderError: 503,
    LLMProviderError: 503,
    VectorStoreError: 503,
}


@app.exception_handler(DomainError)
async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    status_code = 500
    for error_type, mapped_status in ERROR_STATUS_MAP.items():
        if isinstance(exc, error_type):
            status_code = mapped_status
            break
    return JSONResponse(status_code=status_code, content={'error': exc.code, 'message': exc.message})
