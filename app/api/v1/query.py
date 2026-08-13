from fastapi import APIRouter, Depends
from app.api.dependencies import get_query_use_case
from app.api.v1.schemas.query import QueryRequest, QueryResponse, SourceDTO
from app.application.use_cases.query_documents import QueryDocumentsUseCase
from app.domain.entities.query import ChatMessage

router = APIRouter(tags=['query'])


@router.post('/query', response_model=QueryResponse)
async def query_documents(request: QueryRequest, use_case: QueryDocumentsUseCase = Depends(get_query_use_case)) -> QueryResponse:
    messages = [ChatMessage(role=m.role, content=m.content) for m in request.messages]
    result = await use_case.execute(messages, request.top_k)
    return QueryResponse(
        text=result.text,
        id_list=result.id_list,
        sources=[SourceDTO(document_id=s.document_id, title=s.title, score=s.score, text=s.text) for s in result.sources],
        confidence=result.confidence,
        status=result.status,
    )
