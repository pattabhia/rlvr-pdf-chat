"""Context domain entities"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class Source:
    """
    Source document chunk
    
    Represents a chunk of text retrieved from a document.
    """
    chunk_text: str
    page_number: int
    relevance_score: float
    document_name: Optional[str] = None
    document_date: Optional[datetime] = None
    metadata: dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    def is_relevant(self, threshold: float = 0.5) -> bool:
        """Check if source meets relevance threshold"""
        return self.relevance_score >= threshold


@dataclass
class Context:
    """
    Context for answer generation
    
    Represents the retrieved context used to generate an answer.
    """
    chunks: List[Source]
    quality_score: float
    
    def is_sufficient(self, threshold: float = 0.6) -> bool:
        """
        Check if context is sufficient for answer generation
        
        Business rule: Context is sufficient if:
        - Quality score >= threshold
        - At least one chunk
        """
        return self.quality_score >= threshold and len(self.chunks) > 0
    
    def get_text(self) -> str:
        """Get concatenated text from all chunks"""
        return "\n\n".join(chunk.chunk_text for chunk in self.chunks)
    
    def get_top_k(self, k: int) -> List[Source]:
        """Get top k sources by relevance score"""
        return sorted(self.chunks, key=lambda s: s.relevance_score, reverse=True)[:k]

