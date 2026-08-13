from app.domain.ports.job_queue import JobQueue
from app.infrastructure.queue.tasks import index_document_task


class DramatiqJobQueue(JobQueue):
    async def enqueue_index_document(self, document_id: int) -> None:
        index_document_task.send(document_id)
