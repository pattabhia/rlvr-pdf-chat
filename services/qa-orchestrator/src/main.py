"""
QA Orchestrator Service - FastAPI Application

Microservice for question answering using RAG.
Publishes answer.generated events for downstream processing.
"""

import os
import sys
import logging
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Add shared libraries to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../shared'))

from shared.events import EventPublisher, AnswerGeneratedEvent
from shared.observability import setup_observability
from src.qa_service import QAService
from src.llm_adapters import create_llm_adapter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
qa_service: QAService = None
event_publisher: EventPublisher = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI application.
    
    Initializes QA Service and Event Publisher on startup.
    Cleans up on shutdown.
    """
    global qa_service, event_publisher
    
    logger.info("Starting QA Orchestrator Service...")
    
    # Get configuration from environment
    qdrant_url = os.getenv("QDRANT_URL", "http://qdrant:6333")
    qdrant_collection = os.getenv("QDRANT_COLLECTION", "documents")
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    top_k = int(os.getenv("TOP_K", "5"))
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://rlvr:rlvr_password@rabbitmq:5672/")

    # Multi-candidate configuration
    num_candidates = int(os.getenv("NUM_CANDIDATES", "3"))
    candidate_temps_str = os.getenv("CANDIDATE_TEMPERATURES", "0.3,0.7,0.9")
    candidate_temperatures = [float(t.strip()) for t in candidate_temps_str.split(",")]

    # LLM Configuration
    llm_backend = os.getenv("LLM_BACKEND", "ollama")

    # Create LLM adapter based on backend
    if llm_backend == "ollama":
        llm = create_llm_adapter(
            backend="ollama",
            base_url=os.getenv("OLLAMA_URL", "http://ollama:11434"),
            model=os.getenv("OLLAMA_MODEL", "llama3.2:3b"),
            temperature=0.7
        )
    elif llm_backend == "aws_endpoint":
        llm = create_llm_adapter(
            backend="aws_endpoint",
            endpoint_url=os.getenv("AWS_ENDPOINT_URL"),
            api_key=os.getenv("AWS_ENDPOINT_API_KEY"),
            model_name=os.getenv("AWS_ENDPOINT_MODEL_NAME", "custom-model"),
            timeout=60
        )
    elif llm_backend == "huggingface_endpoint":
        llm = create_llm_adapter(
            backend="huggingface_endpoint",
            endpoint_url=os.getenv("HUGGINGFACE_ENDPOINT_URL"),
            api_token=os.getenv("HUGGINGFACE_API_TOKEN"),
            model_name=os.getenv("HUGGINGFACE_MODEL_NAME", "custom-model"),
            timeout=60
        )
    else:
        raise ValueError(f"Unknown LLM_BACKEND: {llm_backend}")

    logger.info(f"Using LLM backend: {llm_backend} ({llm.get_model_name()})")

    # Initialize QA Service
    qa_service = QAService(
        qdrant_url=qdrant_url,
        qdrant_collection=qdrant_collection,
        llm=llm,
        embedding_model=embedding_model,
        top_k=top_k,
        candidate_temperatures=candidate_temperatures
    )
    
    # Initialize Event Publisher
    event_publisher = EventPublisher(rabbitmq_url=rabbitmq_url)
    
    logger.info("QA Orchestrator Service started successfully")
    
    yield
    
    # Cleanup
    logger.info("Shutting down QA Orchestrator Service...")
    if event_publisher:
        event_publisher.close()


# Create FastAPI app
app = FastAPI(
    title="QA Orchestrator Service",
    description="Question Answering service using RAG (Retrieval-Augmented Generation)",
    version="1.0.0",
    lifespan=lifespan
)

# Set up OpenTelemetry observability
tracer, meter = setup_observability(
    app=app,
    service_name="qa-orchestrator",
    service_version="1.0.0"
)


# Request/Response models
class QuestionRequest(BaseModel):
    """Request model for question answering"""
    question: str = Field(..., description="User's question", min_length=1)
    top_k: int | None = Field(None, description="Number of documents to retrieve (optional)", ge=1, le=20)
    publish_event: bool = Field(True, description="Whether to publish answer.generated event")


class MultiCandidateRequest(BaseModel):
    """Request model for multi-candidate answer generation (DPO training)"""
    question: str = Field(..., description="User's question", min_length=1)
    num_candidates: int | None = Field(None, description="Number of candidate answers to generate (uses env default if not specified)", ge=2, le=5)
    top_k: int | None = Field(None, description="Number of documents to retrieve (optional)", ge=1, le=20)
    publish_events: bool = Field(True, description="Whether to publish answer.generated events for each candidate")


class QuestionResponse(BaseModel):
    """Response model for question answering"""
    question: str
    answer: str
    contexts: list[Dict[str, Any]]
    metadata: Dict[str, Any]
    event_published: bool


class MultiCandidateResponse(BaseModel):
    """Response model for multi-candidate answer generation"""
    question: str
    candidates: list[Dict[str, Any]]
    num_candidates: int
    events_published: int


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "qa-orchestrator",
        "version": "1.0.0"
    }


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Answer a question using RAG.
    
    This endpoint:
    1. Retrieves relevant context from vector store
    2. Generates answer using LLM
    3. Publishes answer.generated event (if enabled)
    4. Returns answer with context and metadata
    """
    try:
        logger.info(f"Received question: {request.question}")
        
        # Update top_k if provided
        if request.top_k is not None:
            qa_service.top_k = request.top_k
        
        # Answer question
        result = qa_service.answer_question(request.question)
        
        # Publish event if enabled
        event_published = False
        event_id = None
        if request.publish_event and event_publisher:
            try:
                event = AnswerGeneratedEvent(
                    question=result["question"],
                    answer=result["answer"],
                    contexts=[ctx["content"] for ctx in result["contexts"]],
                    model_name=result["metadata"].get("model", "unknown"),
                    sources=[
                        {
                            "content": ctx["content"],
                            "metadata": ctx["metadata"],
                            "score": ctx["score"]
                        }
                        for ctx in result["contexts"]
                    ]
                )

                event_publisher.publish(
                    event=event,
                    routing_key="answer.generated"
                )

                event_published = True
                event_id = event.event_id
                logger.info(f"Published answer.generated event: {event_id}")
            except Exception as e:
                logger.error(f"Failed to publish event: {e}")
                # Don't fail the request if event publishing fails

        # Add event_id to metadata
        response_metadata = result["metadata"].copy()
        if event_id:
            response_metadata["event_id"] = event_id

        return QuestionResponse(
            question=result["question"],
            answer=result["answer"],
            contexts=result["contexts"],
            metadata=response_metadata,
            event_published=event_published
        )
    
    except Exception as e:
        logger.error(f"Error answering question: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ask/multi-candidate", response_model=MultiCandidateResponse)
async def ask_question_multi_candidate(request: MultiCandidateRequest):
    """
    Generate multiple candidate answers for DPO training.

    This endpoint:
    1. Retrieves relevant context from vector store (once)
    2. Generates multiple candidate answers using LLM
    3. Publishes answer.generated event for each candidate (if enabled)
    4. Returns all candidates with contexts and metadata

    Use this endpoint to generate DPO training pairs:
    - System will verify all candidates with RAGAS
    - Dataset worker will create DPO pairs from candidates with different scores
    """
    try:
        # Use default num_candidates from environment if not specified
        num_cands = request.num_candidates if request.num_candidates is not None else int(os.getenv("NUM_CANDIDATES", "3"))

        logger.info(f"Received multi-candidate request: {request.question} (num_candidates={num_cands})")

        # Update top_k if provided
        if request.top_k is not None:
            qa_service.top_k = request.top_k

        # Generate multiple candidates
        candidates = qa_service.generate_multiple_candidates(
            question=request.question,
            num_candidates=num_cands
        )

        # Publish events for each candidate if enabled
        events_published = 0
        if request.publish_events and event_publisher:
            # Generate a unique batch ID for this multi-candidate request
            import uuid
            batch_id = str(uuid.uuid4())

            for i, candidate in enumerate(candidates):
                try:
                    event = AnswerGeneratedEvent(
                        question=candidate["question"],
                        answer=candidate["answer"],
                        contexts=[ctx["content"] for ctx in candidate["contexts"]],
                        model_name=candidate["metadata"].get("model", "unknown"),
                        temperature=candidate["metadata"].get("temperature", 0.0),
                        candidate_index=i,
                        total_candidates=num_cands,
                        batch_id=batch_id,
                        sources=[
                            {
                                "content": ctx["content"],
                                "metadata": ctx["metadata"],
                                "score": ctx.get("score", 0.0)
                            }
                            for ctx in candidate["contexts"]
                        ]
                    )

                    event_publisher.publish(
                        event=event,
                        routing_key="answer.generated"
                    )

                    # Add event_id to candidate metadata
                    candidate["metadata"]["event_id"] = event.event_id
                    candidate["metadata"]["batch_id"] = batch_id
                    events_published += 1

                    logger.info(f"Published answer.generated event for candidate {i+1}/{num_cands} (batch={batch_id[:8]}): {event.event_id}")
                except Exception as e:
                    logger.error(f"Failed to publish event for candidate {i+1}: {e}")
                    # Don't fail the request if event publishing fails

        return MultiCandidateResponse(
            question=request.question,
            candidates=candidates,
            num_candidates=len(candidates),
            events_published=events_published
        )

    except Exception as e:
        logger.error(f"Error generating multi-candidate answers: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

