"""
Price Range IoU Reward Function

Computes reward based on Intersection over Union (IoU) of price ranges.
Includes scale adjustment to handle order-of-magnitude errors.
"""

import re
import logging
from typing import Dict, Any, Optional, Tuple

from .base import RewardFunction

logger = logging.getLogger(__name__)


class PriceRangeIoUReward(RewardFunction):
    """
    Reward function for pricing questions.
    
    Computes IoU (Intersection over Union) between predicted price range
    and ground truth price range.
    
    Features:
    - Extracts price range from answer text
    - Auto-corrects order-of-magnitude errors (scale adjustment)
    - Returns IoU score (0.0 to 1.0)
    """
    
    def __init__(self, version: str = "1.0"):
        self.version = version
    
    def can_compute(self, question: str, ground_truth: Optional[Dict[str, Any]]) -> bool:
        """
        Check if this is a pricing question with price range ground truth.
        
        Args:
            question: User's question
            ground_truth: Ground truth data
            
        Returns:
            True if this is a pricing question with price range ground truth
        """
        # Check if pricing question
        is_pricing = any(
            word in question.lower()
            for word in ["price", "cost", "rate", "charge", "expensive", "cheap", "how much"]
        )
        
        if not is_pricing:
            return False
        
        # Check if ground truth has price range
        if not ground_truth:
            return False
        
        value = ground_truth.get("value", {})
        has_price_range = "min_price" in value and "max_price" in value
        
        return has_price_range
    
    def compute_reward(
        self,
        question: str,
        answer: str,
        ground_truth: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Compute price range IoU reward.
        
        Args:
            question: User's question
            answer: Generated answer
            ground_truth: Ground truth data with min_price and max_price
            
        Returns:
            Dictionary with reward, reward_type, and debug_info
        """
        # Extract ground truth price range
        value = ground_truth.get("value", {})
        truth_min = value.get("min_price")
        truth_max = value.get("max_price")
        
        if truth_min is None or truth_max is None:
            logger.warning(f"Ground truth missing price range: {ground_truth}")
            return {
                "reward": 0.0,
                "reward_type": "price_range_iou",
                "reward_function_version": self.version,
                "debug_info": {
                    "error": "Ground truth missing price range",
                    "truth_range": None,
                    "pred_range_raw": None,
                    "pred_range_used": None,
                    "scale_factor": 1,
                    "iou": 0.0
                }
            }
        
        truth_range = (truth_min, truth_max)
        
        # Extract predicted price range from answer
        pred_range_raw = self._extract_price_range(answer)
        
        if pred_range_raw is None:
            logger.debug(f"Could not extract price range from answer: {answer[:100]}")
            return {
                "reward": 0.0,
                "reward_type": "price_range_iou",
                "reward_function_version": self.version,
                "debug_info": {
                    "truth_range": list(truth_range),
                    "pred_range_raw": None,
                    "pred_range_used": None,
                    "scale_factor": 1,
                    "iou": 0.0,
                    "message": "No price range extracted from answer"
                }
            }
        
        # Apply scale adjustment to fix order-of-magnitude errors
        pred_range_used, scale_factor = self._maybe_rescale(pred_range_raw, truth_range)
        
        # Compute IoU
        iou = self._compute_iou(pred_range_used, truth_range)
        
        logger.info(
            f"Price Range IoU: raw={pred_range_raw}, "
            f"scaled={pred_range_used} (factor={scale_factor}), "
            f"truth={truth_range}, "
            f"iou={iou:.3f}"
        )
        
        return {
            "reward": iou,
            "reward_type": "price_range_iou",
            "reward_function_version": self.version,
            "debug_info": {
                "truth_range": list(truth_range),
                "pred_range_raw": list(pred_range_raw),
                "pred_range_used": list(pred_range_used) if pred_range_used else None,
                "scale_factor": scale_factor,
                "iou": iou
            }
        }
    
    def _extract_price_range(self, answer: str) -> Optional[Tuple[int, int]]:
        """
        Extract price range from answer text.
        
        Looks for patterns like:
        - ₹24,000 – ₹65,000
        - Rs 24000 to Rs 65000
        - 24,000 - 65,000
        
        Args:
            answer: Answer text containing price information
            
        Returns:
            Tuple of (min_price, max_price) or None if not found
        """
        # Pattern to match Indian currency numbers
        # Handles: ₹24,000 or 24000 or Rs 24,000
        nums = re.findall(r'[₹Rs.\s]*([\d,]+)', answer)

        if len(nums) < 2:
            return None

        # Convert to integers
        vals = []
        for num_str in nums:
            try:
                val = int(num_str.replace(',', ''))
                vals.append(val)
            except ValueError:
                continue

        if len(vals) < 2:
            return None

        # Return min and max
        return min(vals), max(vals)

    def _maybe_rescale(
        self,
        pred_range: Optional[Tuple[int, int]],
        truth_range: Tuple[int, int]
    ) -> Tuple[Optional[Tuple[int, int]], int]:
        """
        Auto-correct order-of-magnitude errors in price extraction.

        This handles common OCR/LLM errors where digits are misread:
        - 2,400 → 24,000 (missing a zero)
        - 240 → 24,000 (missing two zeros)

        The function detects when the predicted range is consistently smaller
        than the truth range by an order of magnitude, and scales it up.

        Args:
            pred_range: Predicted (min, max) price range
            truth_range: Ground truth (min, max) price range

        Returns:
            Tuple of (adjusted_range, scale_factor)
        """
        if pred_range is None:
            return None, 1

        pmin, pmax = pred_range
        tmin, tmax = truth_range

        # If prediction is consistently smaller by an order of magnitude
        if pmax < tmin and len(str(tmin)) - len(str(pmax)) >= 1:
            factor = 10 ** (len(str(tmin)) - len(str(pmax)))
            logger.info(
                f"Scale adjustment: {pred_range} → ({pmin * factor}, {pmax * factor}) "
                f"(factor={factor})"
            )
            return (pmin * factor, pmax * factor), factor

        return pred_range, 1

    def _compute_iou(
        self,
        pred_range: Optional[Tuple[int, int]],
        truth_range: Tuple[int, int]
    ) -> float:
        """
        Compute IoU (Intersection over Union) for price ranges.

        Args:
            pred_range: Predicted (min, max) price range
            truth_range: Ground truth (min, max) price range

        Returns:
            IoU score between 0.0 and 1.0
        """
        if pred_range is None:
            return 0.0

        pmin, pmax = pred_range
        tmin, tmax = truth_range

        # Compute intersection
        overlap_min = max(pmin, tmin)
        overlap_max = min(pmax, tmax)

        if overlap_min >= overlap_max:
            # No overlap
            return 0.0

        # Compute IoU (Intersection over Union)
        overlap = overlap_max - overlap_min
        union = max(pmax, tmax) - min(pmin, tmin)

        if union <= 0:
            return 0.0

        iou = overlap / union

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, iou))

