from app.application.services.confidence_service import ConfidenceService
from app.domain.entities.source import Source


def test_confidence_zero_without_sources():
    service = ConfidenceService(min_score=0.35, answer_threshold=0.45)
    assert service.calculate([]) == 0.0


def test_confidence_uses_scores():
    service = ConfidenceService(min_score=0.35, answer_threshold=0.45)
    confidence = service.calculate([Source(document_id=1, title='t', score=0.8, text='x')])
    assert confidence == 0.8
