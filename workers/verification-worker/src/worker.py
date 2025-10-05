"""
Verification Worker - Consumes answer.generated events and publishes verification.completed events

This worker:
1. Consumes answer.generated events from RabbitMQ
2. Verifies answer quality using RAGAS
3. Publishes verification.completed events
"""

import os
import sys
import logging
import time
from typing import Dict, Any

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.events.consumer import EventConsumer
from shared.events.publisher import EventPublisher
from shared.events.schemas import AnswerGeneratedEvent, VerificationCompletedEvent
from src.ragas_verifier import RagasVerifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class VerificationWorker:
    """
    Worker that verifies answer quality using RAGAS.
    
    Workflow:
    1. Consume answer.generated event
    2. Verify answer quality (faithfulness, relevancy)
    3. Publish verification.completed event
    """
    
    def __init__(
        self,
        rabbitmq_url: str,
        verification_mode: str = "ollama",
        ollama_url: str = "http://ollama:11434",
        ollama_model: str = "llama3.2:3b",
        faithfulness_threshold: float = 0.7,
        relevancy_threshold: float = 0.7
    ):
        """
        Initialize Verification Worker.
        
        Args:
            rabbitmq_url: RabbitMQ connection URL
            verification_mode: 'ollama' or 'heuristic'
            ollama_url: Ollama server URL
            ollama_model: Model name for RAGAS
            faithfulness_threshold: Threshold for high confidence
            relevancy_threshold: Threshold for high confidence
        """
        self.rabbitmq_url = rabbitmq_url
        
        # Initialize RAGAS verifier
        self.verifier = RagasVerifier(
            mode=verification_mode,
            ollama_url=ollama_url,
            ollama_model=ollama_model,
            faithfulness_threshold=faithfulness_threshold,
            relevancy_threshold=relevancy_threshold
        )
        
        # Initialize event consumer and publisher
        self.consumer = EventConsumer(rabbitmq_url=rabbitmq_url)
        self.publisher = EventPublisher(rabbitmq_url=rabbitmq_url)
        
        logger.info("Verification Worker initialized")
    
    def process_answer_generated(self, event: AnswerGeneratedEvent) -> None:
        """
        Process answer.generated event.
        
        Args:
            event: AnswerGeneratedEvent to process
        """
        try:
            logger.info(f"Processing answer.generated event: {event.event_id}")
            
            # Extract contexts (list of strings)
            contexts = [ctx.get("content", "") for ctx in event.contexts if isinstance(ctx, dict)]
            
            if not contexts:
                logger.warning(f"No contexts found in event {event.event_id}")
                contexts = [""]
            
            # Verify answer quality
            verification_result = self.verifier.verify(
                question=event.question,
                answer=event.answer,
                contexts=contexts
            )
            
            logger.info(
                f"Verification complete: faithfulness={verification_result['faithfulness']:.3f}, "
                f"relevancy={verification_result['relevancy']:.3f}, "
                f"confidence={verification_result['confidence']}"
            )
            
            # Create verification.completed event
            verification_event = VerificationCompletedEvent(
                request_id=event.event_id,
                question=event.question,
                answer=event.answer,
                faithfulness_score=verification_result["faithfulness"],
                relevancy_score=verification_result["relevancy"],
                overall_score=verification_result["overall_score"],
                verification_model=verification_result["mode"]
            )
            
            # Publish verification.completed event
            self.publisher.publish(
                event=verification_event,
                routing_key="verification.completed"
            )
            
            logger.info(f"Published verification.completed event: {verification_event.event_id}")
            
        except Exception as e:
            logger.error(f"Error processing answer.generated event: {e}", exc_info=True)
    
    def start(self):
        """Start consuming answer.generated events."""
        logger.info("Starting Verification Worker...")
        logger.info("Waiting for answer.generated events...")

        # Subscribe to answer.generated events using decorator
        @self.consumer.subscribe("answer.generated")
        def handle_answer_generated(event: AnswerGeneratedEvent):
            self.process_answer_generated(event)

        # Start consuming
        self.consumer.start()


def main():
    """Main entry point."""
    # Load configuration from environment
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://rlvr:rlvr_password@rabbitmq:5672/")
    verification_mode = os.getenv("VERIFICATION_MODE", "ollama")
    ollama_url = os.getenv("OLLAMA_URL", "http://ollama:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    faithfulness_threshold = float(os.getenv("FAITHFULNESS_THRESHOLD", "0.7"))
    relevancy_threshold = float(os.getenv("RELEVANCY_THRESHOLD", "0.7"))
    
    # Create and start worker
    worker = VerificationWorker(
        rabbitmq_url=rabbitmq_url,
        verification_mode=verification_mode,
        ollama_url=ollama_url,
        ollama_model=ollama_model,
        faithfulness_threshold=faithfulness_threshold,
        relevancy_threshold=relevancy_threshold
    )
    
    # Start consuming events
    worker.start()


if __name__ == "__main__":
    main()

