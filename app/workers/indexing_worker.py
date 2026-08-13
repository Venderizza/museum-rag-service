# Importing tasks registers Dramatiq actors.
from app.infrastructure.queue.tasks import index_document_task

__all__ = ['index_document_task']
