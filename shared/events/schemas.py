"""
Event Schemas for RLVR Platform

All events follow a consistent structure:
- event_id: Unique identifier
- event_type: Type of event
- timestamp: When the event occurred
- payload: Event-specific data
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4


@dataclass
class BaseEvent:
    """Base class for all events"""
    event_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary"""
        return asdict(self)


@dataclass
class AnswerGeneratedEvent(BaseEvent):
    """
    Published when: Question Answering Service generates an answer
    Consumed by: Verification Worker, Reward Computation Worker, Dataset Generation Worker
    """
    event_type: str = "answer.generated"
    
    # Core data
    question: str = ""
    answer: str = ""
    contexts: List[str] = field(default_factory=list)
    
    # Metadata
    request_id: str = ""
    session_id: Optional[str] = None
    model_name: str = ""
    temperature: float = 0.0
    
    # Sources
    sources: List[Dict[str, Any]] = field(default_factory=list)
    
    # Confidence
    confidence: str = "MEDIUM"  # HIGH, MEDIUM, LOW


@dataclass
class VerificationCompletedEvent(BaseEvent):
    """
    Published when: Verification Worker completes RAGAS verification
    Consumed by: Dataset Generation Worker
    """
    event_type: str = "verification.completed"
    
    # Reference to original question
    request_id: str = ""
    question: str = ""
    answer: str = ""
    
    # RAGAS scores
    faithfulness_score: float = 0.0
    relevancy_score: float = 0.0
    overall_score: float = 0.0
    
    # Metadata
    verification_model: str = ""
    verification_duration_ms: int = 0


@dataclass
class RewardComputedEvent(BaseEvent):
    """
    Published when: Reward Computation Worker computes reward
    Consumed by: Dataset Generation Worker
    """
    event_type: str = "reward.computed"
    
    # Reference to original question
    request_id: str = ""
    question: str = ""
    answer: str = ""
    
    # Reward
    reward: Optional[float] = None
    reward_type: str = ""  # price_range_iou, menu_match, etc.
    reward_function_version: str = ""
    
    # Ground truth used
    ground_truth: Optional[Dict[str, Any]] = None
    ground_truth_domain: Optional[str] = None
    ground_truth_key: Optional[str] = None
    
    # Debug info
    debug_info: Dict[str, Any] = field(default_factory=dict)
    
    # Reason if reward is None
    reason: Optional[str] = None  # no_ground_truth_domain_detected, ground_truth_not_found, etc.


@dataclass
class DatasetEntryCreatedEvent(BaseEvent):
    """
    Published when: Dataset Generation Worker creates a training data entry
    Consumed by: Analytics Service (future)
    """
    event_type: str = "dataset.entry_created"
    
    # Reference
    request_id: str = ""
    
    # File info
    file_path: str = ""
    entry_number: int = 0
    
    # Quality indicators
    has_verification: bool = False
    has_reward: bool = False
    reward_value: Optional[float] = None


@dataclass
class DocumentIngestedEvent(BaseEvent):
    """
    Published when: Document Ingestion Service processes a PDF
    Consumed by: Analytics Service (future)
    """
    event_type: str = "document.ingested"
    
    # Document info
    document_id: str = ""
    filename: str = ""
    num_pages: int = 0
    num_chunks: int = 0
    
    # Processing info
    processing_duration_ms: int = 0
    embedding_model: str = ""
    
    # Status
    status: str = "success"  # success, failed, partial
    error_message: Optional[str] = None


# Event type registry for deserialization
EVENT_REGISTRY = {
    "answer.generated": AnswerGeneratedEvent,
    "verification.completed": VerificationCompletedEvent,
    "reward.computed": RewardComputedEvent,
    "dataset.entry_created": DatasetEntryCreatedEvent,
    "document.ingested": DocumentIngestedEvent,
}


def deserialize_event(event_dict: Dict[str, Any]) -> BaseEvent:
    """
    Deserialize event dictionary to appropriate event class
    
    Args:
        event_dict: Event data as dictionary
        
    Returns:
        Event instance
        
    Raises:
        ValueError: If event_type is unknown
    """
    event_type = event_dict.get("event_type")
    if event_type not in EVENT_REGISTRY:
        raise ValueError(f"Unknown event type: {event_type}")
    
    event_class = EVENT_REGISTRY[event_type]
    return event_class(**event_dict)

