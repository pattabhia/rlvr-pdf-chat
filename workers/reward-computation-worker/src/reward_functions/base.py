"""Base class for reward functions"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class RewardFunction(ABC):
    """
    Base class for reward functions.
    
    Each reward function computes a score (0.0 to 1.0) based on
    comparing the generated answer with ground truth.
    """
    
    @abstractmethod
    def compute_reward(
        self,
        question: str,
        answer: str,
        ground_truth: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute reward for an answer.
        
        Args:
            question: User's question
            answer: Generated answer
            ground_truth: Ground truth data from Ground Truth Service
            
        Returns:
            Dictionary with:
            - reward: Float score (0.0 to 1.0)
            - reward_type: Type of reward (e.g., "price_range_iou")
            - debug_info: Additional debug information
        """
        pass
    
    @abstractmethod
    def can_compute(self, question: str, ground_truth: Optional[Dict[str, Any]]) -> bool:
        """
        Check if this reward function can compute a reward for this question.
        
        Args:
            question: User's question
            ground_truth: Ground truth data (may be None)
            
        Returns:
            True if this reward function can compute a reward
        """
        pass

