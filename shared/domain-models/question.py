"""Question domain entity"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Question:
    """
    Question domain entity
    
    Represents a user's question in the RAG system.
    """
    text: str
    session_id: Optional[str] = None
    
    def __post_init__(self):
        """Validate question"""
        if not self.text or not self.text.strip():
            raise ValueError("Question text cannot be empty")
        
        # Normalize whitespace
        self.text = " ".join(self.text.split())
    
    def __str__(self) -> str:
        return self.text
    
    def is_pricing_question(self) -> bool:
        """Check if this is a pricing-related question"""
        pricing_keywords = ["price", "cost", "rate", "tariff", "charge", "fee"]
        text_lower = self.text.lower()
        return any(keyword in text_lower for keyword in pricing_keywords)
    
    def is_menu_question(self) -> bool:
        """Check if this is a menu-related question"""
        menu_keywords = ["menu", "dish", "cuisine", "restaurant", "food"]
        text_lower = self.text.lower()
        return any(keyword in text_lower for keyword in menu_keywords)

