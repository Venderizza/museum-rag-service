from abc import ABC, abstractmethod


class JobQueue(ABC):
    @abstractmethod
    async def enqueue_index_document(self, document_id: int) -> None: ...
