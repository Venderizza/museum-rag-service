from app.domain.entities.chunk import Chunk


class ChunkingService:
    def __init__(self, chunk_size_tokens: int, chunk_overlap_tokens: int):
        self.chunk_size_tokens = chunk_size_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens

    def split(
        self,
        *,
        document_id: int,
        body: str,
        embedding_model_name: str,
        embedding_dimension: int,
        embedding_version: str,
    ) -> list[Chunk]:
        text = body.strip()
        if not text:
            return []

        # MVP tokenizer approximation: word-based. Replace with tokenizer-specific implementation later.
        words = text.split()
        if len(words) <= self.chunk_size_tokens:
            return [Chunk(
                document_id=document_id,
                chunk_index=0,
                text=text,
                char_start=0,
                char_end=len(text),
                token_count=len(words),
                embedding_model_name=embedding_model_name,
                embedding_dimension=embedding_dimension,
                embedding_version=embedding_version,
            )]

        chunks: list[Chunk] = []
        start_word = 0
        chunk_index = 0
        step = max(1, self.chunk_size_tokens - self.chunk_overlap_tokens)
        while start_word < len(words):
            end_word = min(len(words), start_word + self.chunk_size_tokens)
            chunk_words = words[start_word:end_word]
            chunk_text = ' '.join(chunk_words)
            # char offsets are approximate in this MVP implementation.
            char_start = len(' '.join(words[:start_word])) + (1 if start_word > 0 else 0)
            char_end = char_start + len(chunk_text)
            chunks.append(Chunk(
                document_id=document_id,
                chunk_index=chunk_index,
                text=chunk_text,
                char_start=char_start,
                char_end=char_end,
                token_count=len(chunk_words),
                embedding_model_name=embedding_model_name,
                embedding_dimension=embedding_dimension,
                embedding_version=embedding_version,
            ))
            chunk_index += 1
            if end_word == len(words):
                break
            start_word += step
        return chunks

    @staticmethod
    def build_embedding_text(title: str, chunk_text: str) -> str:
        return f'Название экспоната: {title}\n\nТекст:\n{chunk_text}'
