from app.domain.entities.source import Source


class ConfidenceService:
    def __init__(self, min_score: float, answer_threshold: float):
        self.min_score = min_score
        self.answer_threshold = answer_threshold

    def calculate(self, sources: list[Source]) -> float:
        if not sources:
            return 0.0
        scores = sorted((max(0.0, min(1.0, source.score)) for source in sources), reverse=True)
        top = scores[:3]
        max_score = top[0]
        avg_top = sum(top) / len(top)
        return round((0.7 * max_score) + (0.3 * avg_top), 4)

    def has_enough_confidence(self, confidence: float) -> bool:
        return confidence >= self.answer_threshold
