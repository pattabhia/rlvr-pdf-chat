"""
Shared Event Library for RLVR Platform

This package contains event schemas and event bus utilities
used across all services and workers.
"""

from .schemas import (
    AnswerGeneratedEvent,
    VerificationCompletedEvent,
    RewardComputedEvent,
    DatasetEntryCreatedEvent,
    DocumentIngestedEvent,
)

from .publisher import EventPublisher
from .consumer import EventConsumer

__all__ = [
    # Event Schemas
    "AnswerGeneratedEvent",
    "VerificationCompletedEvent",
    "RewardComputedEvent",
    "DatasetEntryCreatedEvent",
    "DocumentIngestedEvent",
    # Event Bus
    "EventPublisher",
    "EventConsumer",
]

