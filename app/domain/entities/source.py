from dataclasses import dataclass


@dataclass(slots=True)
class Source:
    document_id: int
    title: str
    score: float
    text: str
