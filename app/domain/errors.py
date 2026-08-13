class DomainError(Exception):
    code = 'domain_error'
    message = 'Domain error'

    def __init__(self, message: str | None = None):
        super().__init__(message or self.message)
        self.message = message or self.message


class DocumentAlreadyExistsError(DomainError):
    code = 'document_already_exists'
    message = 'Document with this document_id already exists'


class DocumentNotFoundError(DomainError):
    code = 'document_not_found'
    message = 'Document not found'


class DocumentAlreadyDeletedError(DomainError):
    code = 'document_already_deleted'
    message = 'Document is already deleted'


class DocumentDeletedError(DomainError):
    code = 'document_deleted'
    message = 'Document is deleted'


class DocumentNotIndexedError(DomainError):
    code = 'document_not_indexed'
    message = 'Document is not indexed'


class IndexingError(DomainError):
    code = 'indexing_error'
    message = 'Indexing error'


class ChunkingError(DomainError):
    code = 'chunking_error'
    message = 'Chunking error'


class EmbeddingProviderError(DomainError):
    code = 'embedding_provider_error'
    message = 'Embedding provider error'


class VectorStoreError(DomainError):
    code = 'vector_store_error'
    message = 'Vector store error'


class EmptyQueryError(DomainError):
    code = 'empty_query'
    message = 'Query is empty'


class NoRelevantSourcesError(DomainError):
    code = 'no_relevant_sources'
    message = 'No relevant sources found'


class LLMProviderError(DomainError):
    code = 'llm_provider_error'
    message = 'LLM provider error'


class ConfigurationError(DomainError):
    code = 'configuration_error'
    message = 'Configuration error'


class ExternalProviderUnavailableError(DomainError):
    code = 'external_provider_unavailable'
    message = 'External provider is unavailable'


class InternalApplicationError(DomainError):
    code = 'internal_error'
    message = 'Internal application error'
