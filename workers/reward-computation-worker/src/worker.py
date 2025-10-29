"""
Reward Computation Worker

Consumes answer.generated events, computes verifiable rewards,
and publishes reward.computed events.
"""

import os
import sys
import logging
import httpx
from typing import Dict, Any, Optional

# Add shared libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from shared.events import EventConsumer, EventPublisher, AnswerGeneratedEvent, RewardComputedEvent
from src.domain_detector import DomainDetector
from src.reward_functions import PriceRangeIoUReward

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RewardComputationWorker:
    """
    Worker that computes verifiable rewards for RLVR training.
    
    Flow:
    1. Consume answer.generated events
    2. Detect domain (e.g., taj_hotels_pricing)
    3. Fetch ground truth from Ground Truth Service
    4. Compute reward using appropriate reward function
    5. Publish reward.computed event
    """
    
    def __init__(
        self,
        rabbitmq_url: str,
        ground_truth_service_url: str
    ):
        self.rabbitmq_url = rabbitmq_url
        self.ground_truth_service_url = ground_truth_service_url
        
        # Initialize components
        self.domain_detector = DomainDetector(ground_truth_service_url=ground_truth_service_url)
        self.reward_functions = {
            "price_range_iou": PriceRangeIoUReward(version="1.0")
        }
        
        # Initialize event consumer and publisher
        self.consumer = EventConsumer(
            rabbitmq_url=rabbitmq_url,
            queue_name="reward-computation-queue"
        )
        self.publisher = EventPublisher(rabbitmq_url=rabbitmq_url)
        
        # HTTP client for Ground Truth Service
        self.http_client = httpx.Client(
            base_url=ground_truth_service_url,
            timeout=10.0
        )
        
        logger.info("Reward Computation Worker initialized")
    
    def start(self):
        """Start consuming events"""
        logger.info("Starting Reward Computation Worker...")
        
        # Connect publisher
        self.publisher.connect()
        
        # Subscribe to answer.generated events
        @self.consumer.subscribe("answer.generated")
        def handle_answer_generated(event: AnswerGeneratedEvent):
            self._process_answer(event)
        
        # Start consuming
        self.consumer.start()
    
    def _process_answer(self, event: AnswerGeneratedEvent):
        """
        Process an answer.generated event.
        
        Args:
            event: AnswerGeneratedEvent with question, answer, contexts, etc.
        """
        logger.info(f"Processing answer for question: {event.question[:50]}...")
        
        # Step 1: Detect domain
        domain_result = self.domain_detector.detect_domain(
            question=event.question,
            answer=event.answer
        )
        
        if domain_result is None:
            logger.info("No verifiable domain detected - skipping reward computation")
            # Publish event with reward=None to indicate no ground truth
            self._publish_no_reward_event(event)
            return
        
        domain_name, entity_key = domain_result
        logger.info(f"Detected domain: {domain_name}, entity: {entity_key}")
        
        # Step 2: Fetch ground truth
        ground_truth = self._fetch_ground_truth(domain_name, entity_key)
        
        if ground_truth is None:
            logger.warning(f"No ground truth found for {domain_name}/{entity_key}")
            self._publish_no_reward_event(event)
            return
        
        # Step 3: Select appropriate reward function
        reward_function = self._select_reward_function(event.question, ground_truth)
        
        if reward_function is None:
            logger.warning(f"No reward function available for {domain_name}")
            self._publish_no_reward_event(event)
            return
        
        # Step 4: Compute reward
        reward_result = reward_function.compute_reward(
            question=event.question,
            answer=event.answer,
            ground_truth=ground_truth
        )
        
        # Step 5: Publish reward.computed event
        self._publish_reward_event(event, reward_result, ground_truth)
    
    def _fetch_ground_truth(self, domain: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Fetch ground truth from Ground Truth Service.
        
        Args:
            domain: Domain name (e.g., "taj_hotels_pricing")
            key: Entity key (e.g., "taj mahal palace")
            
        Returns:
            Ground truth data or None if not found
        """
        try:
            response = self.http_client.get(f"/ground-truth/{domain}/{key}")
            
            if response.status_code == 404:
                logger.warning(f"Ground truth not found: {domain}/{key}")
                return None
            
            response.raise_for_status()
            return response.json()
        
        except Exception as e:
            logger.error(f"Error fetching ground truth: {e}")
            return None

    def _select_reward_function(
        self,
        question: str,
        ground_truth: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Select appropriate reward function based on question and ground truth.

        Args:
            question: User's question
            ground_truth: Ground truth data

        Returns:
            Reward function instance or None
        """
        # Try each reward function
        for reward_func in self.reward_functions.values():
            if reward_func.can_compute(question, ground_truth):
                return reward_func

        return None

    def _publish_reward_event(
        self,
        original_event: AnswerGeneratedEvent,
        reward_result: Dict[str, Any],
        ground_truth: Dict[str, Any]
    ):
        """
        Publish reward.computed event.

        Args:
            original_event: Original answer.generated event
            reward_result: Result from reward function
            ground_truth: Ground truth data
        """
        event = RewardComputedEvent(
            question=original_event.question,
            answer=original_event.answer,
            reward=reward_result["reward"],
            reward_type=reward_result["reward_type"],
            reward_function_version=reward_result["reward_function_version"],
            ground_truth=ground_truth,
            debug_info=reward_result.get("debug_info", {})
        )

        self.publisher.publish(event, routing_key="reward.computed")
        logger.info(f"Published reward.computed event: reward={event.reward:.3f}")

    def _publish_no_reward_event(self, original_event: AnswerGeneratedEvent):
        """
        Publish reward.computed event with reward=None (no ground truth).

        Args:
            original_event: Original answer.generated event
        """
        event = RewardComputedEvent(
            question=original_event.question,
            answer=original_event.answer,
            reward=None,
            reward_type="none",
            reward_function_version="1.0",
            ground_truth=None,
            debug_info={"message": "No verifiable ground truth available"}
        )

        self.publisher.publish(event, routing_key="reward.computed")
        logger.info("Published reward.computed event: no ground truth")


def main():
    """Main entry point"""
    # Get configuration from environment
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://rlvr:rlvr_password@rabbitmq:5672/")
    ground_truth_service_url = os.getenv("GROUND_TRUTH_SERVICE_URL", "http://ground-truth:8007")

    # Create and start worker
    worker = RewardComputationWorker(
        rabbitmq_url=rabbitmq_url,
        ground_truth_service_url=ground_truth_service_url
    )

    try:
        worker.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
