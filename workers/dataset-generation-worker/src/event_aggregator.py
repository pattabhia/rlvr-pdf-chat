"""
Event Aggregator - Aggregates related events for training data generation

Combines:
- answer.generated events
- verification.completed events
- reward.computed events

Into complete training data entries.
"""

import logging
from typing import Dict, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class EventAggregator:
    """
    Aggregates related events for training data generation.
    
    Stores events in memory and matches them by question+answer.
    When all three event types are received for a question, creates a complete entry.
    """
    
    def __init__(self, timeout_minutes: int = 5):
        """
        Initialize event aggregator.
        
        Args:
            timeout_minutes: How long to wait for all events before timing out
        """
        self.timeout_minutes = timeout_minutes
        
        # Storage: key = (question, answer), value = dict of events
        self.pending_entries: Dict[tuple, Dict] = {}
        
        logger.info(f"Event Aggregator initialized (timeout={timeout_minutes}m)")
    
    def _get_key(self, question: str, answer: str) -> tuple:
        """Generate unique key for question+answer pair."""
        return (question.strip(), answer.strip())
    
    def add_answer_generated(self, event) -> Optional[Dict]:
        """
        Add answer.generated event.
        
        Args:
            event: AnswerGeneratedEvent
            
        Returns:
            Complete entry if all events received, None otherwise
        """
        key = self._get_key(event.question, event.answer)
        
        if key not in self.pending_entries:
            self.pending_entries[key] = {
                "question": event.question,
                "answer": event.answer,
                "contexts": event.contexts,
                "model_name": event.model_name,
                "sources": event.sources,
                "timestamp": event.timestamp,
                "answer_event_id": event.event_id,
            }
        else:
            # Update if not already set
            entry = self.pending_entries[key]
            if "answer_event_id" not in entry:
                entry["answer_event_id"] = event.event_id
                entry["contexts"] = event.contexts
                entry["model_name"] = event.model_name
                entry["sources"] = event.sources
        
        return self._check_complete(key)
    
    def add_verification_completed(self, event) -> Optional[Dict]:
        """
        Add verification.completed event.
        
        Args:
            event: VerificationCompletedEvent
            
        Returns:
            Complete entry if all events received, None otherwise
        """
        key = self._get_key(event.question, event.answer)
        
        if key not in self.pending_entries:
            self.pending_entries[key] = {
                "question": event.question,
                "answer": event.answer,
                "timestamp": event.timestamp,
            }
        
        # Add verification data
        entry = self.pending_entries[key]
        entry["verification"] = {
            "faithfulness_score": event.faithfulness_score,
            "relevancy_score": event.relevancy_score,
            "overall_score": event.overall_score,
            "verification_model": event.verification_model,
        }
        entry["verification_event_id"] = event.event_id
        
        return self._check_complete(key)
    
    def add_reward_computed(self, event) -> Optional[Dict]:
        """
        Add reward.computed event.
        
        Args:
            event: RewardComputedEvent
            
        Returns:
            Complete entry if all events received, None otherwise
        """
        key = self._get_key(event.question, event.answer)
        
        if key not in self.pending_entries:
            self.pending_entries[key] = {
                "question": event.question,
                "answer": event.answer,
                "timestamp": event.timestamp,
            }
        
        # Add reward data
        entry = self.pending_entries[key]
        entry["reward"] = {
            "score": event.reward,
            "reward_type": event.reward_type,
            "reward_function_version": event.reward_function_version,
            "ground_truth_domain": event.ground_truth_domain,
            "ground_truth_key": event.ground_truth_key,
            "reason": event.reason,
        }
        entry["reward_event_id"] = event.event_id
        
        return self._check_complete(key)
    
    def _check_complete(self, key: tuple) -> Optional[Dict]:
        """
        Check if entry has all required events.

        Args:
            key: Entry key (question, answer)

        Returns:
            Complete entry if all events received, None otherwise
        """
        entry = self.pending_entries.get(key)
        if not entry:
            return None

        # Check if we have all required event types
        # Reward is optional - we can create entries with just answer + verification
        has_answer = "answer_event_id" in entry
        has_verification = "verification" in entry
        has_reward = "reward" in entry

        # Complete if we have answer + verification (reward is optional)
        if has_answer and has_verification:
            # Complete! Remove from pending and return
            logger.info(f"✅ Complete entry: {entry['question'][:50]}... (has_reward={has_reward})")
            del self.pending_entries[key]
            return entry

        return None
    
    def cleanup_expired(self) -> int:
        """
        Remove entries that have timed out.
        
        Returns:
            Number of entries removed
        """
        now = datetime.utcnow()
        timeout_delta = timedelta(minutes=self.timeout_minutes)
        
        expired_keys = []
        for key, entry in self.pending_entries.items():
            entry_time = datetime.fromisoformat(entry["timestamp"])
            if now - entry_time > timeout_delta:
                expired_keys.append(key)
        
        for key in expired_keys:
            logger.warning(f"Removing expired entry: {self.pending_entries[key]['question'][:50]}...")
            del self.pending_entries[key]
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict:
        """Get statistics about pending entries."""
        return {
            "pending_entries": len(self.pending_entries),
            "timeout_minutes": self.timeout_minutes,
        }

