"""
Document Ingestion Service - FastAPI REST API

Provides endpoints for:
- PDF upload and processing
- Document management
- Collection statistics
"""

import os
import sys
import logging
import time
import uuid
from typing import List
from datetime import datetime

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Add shared directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from src.pdf_processor import PDFProcessor
from src.text_chunker import TextChunker
from src.embedding_service import EmbeddingService, BatchEmbeddingProcessor
from src.vector_store import VectorStore
from shared.events.publisher import EventPublisher
from shared.events.schemas import DocumentIngestedEvent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Document Ingestion Service",
    description="PDF processing and vector store ingestion",
    version="1.0.0"
)

# Initialize components
pdf_processor = None
text_chunker = None
embedding_service = None
batch_processor = None
vector_store = None
event_publisher = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global pdf_processor, text_chunker, embedding_service, batch_processor, vector_store, event_publisher
    
    logger.info("Starting Document Ingestion Service...")
    
    # Load configuration from environment
    qdrant_host = os.getenv("QDRANT_HOST", "qdrant")
    qdrant_port = int(os.getenv("QDRANT_PORT", "6333"))
    qdrant_collection = os.getenv("QDRANT_COLLECTION", "documents")
    embedding_model = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    chunk_size = int(os.getenv("CHUNK_SIZE", "1000"))
    chunk_overlap = int(os.getenv("CHUNK_OVERLAP", "200"))
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://rlvr:rlvr_password@rabbitmq:5672/")
    
    # Initialize components
    pdf_processor = PDFProcessor()
    text_chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    embedding_service = EmbeddingService(model_name=embedding_model)
    batch_processor = BatchEmbeddingProcessor(embedding_service=embedding_service)
    vector_store = VectorStore(
        host=qdrant_host,
        port=qdrant_port,
        collection_name=qdrant_collection,
        vector_dimension=embedding_service.get_dimension()
    )
    event_publisher = EventPublisher(rabbitmq_url=rabbitmq_url)
    
    logger.info("Document Ingestion Service started successfully")


# Response models
class IngestResponse(BaseModel):
    """Response for document ingestion."""
    document_id: str
    filename: str
    num_pages: int
    num_chunks: int
    processing_duration_ms: int
    status: str


class CollectionInfoResponse(BaseModel):
    """Response for collection info."""
    collection_name: str
    vectors_count: int
    points_count: int
    vector_dimension: int
    distance: str


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "Document Ingestion Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health():
    """Health check with component status."""
    return {
        "status": "healthy",
        "components": {
            "pdf_processor": pdf_processor is not None,
            "text_chunker": text_chunker is not None,
            "embedding_service": embedding_service is not None,
            "vector_store": vector_store is not None,
            "event_publisher": event_publisher is not None
        }
    }


@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingest a PDF document.
    
    Steps:
    1. Extract text from PDF
    2. Chunk text into segments
    3. Generate embeddings
    4. Store in vector database
    5. Publish event
    """
    start_time = time.time()
    document_id = str(uuid.uuid4())
    
    try:
        logger.info(f"Ingesting document: {file.filename} (document_id={document_id})")
        
        # Read file bytes
        file_bytes = await file.read()
        
        # Step 1: Extract text from PDF
        pages = pdf_processor.extract_text(file_bytes, filename=file.filename)
        
        if not pages:
            raise HTTPException(status_code=400, detail="No text extracted from PDF")
        
        # Step 2: Chunk text
        chunks = text_chunker.chunk_pages(pages, source_name=file.filename)
        
        if not chunks:
            raise HTTPException(status_code=400, detail="No chunks created from PDF")
        
        # Step 3: Generate embeddings
        chunks_with_embeddings = batch_processor.process_chunks(chunks)
        
        # Step 4: Store in vector database
        num_added = vector_store.add_chunks(chunks_with_embeddings, document_id=document_id)
        
        # Calculate processing duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Step 5: Publish event
        event = DocumentIngestedEvent(
            document_id=document_id,
            filename=file.filename,
            num_pages=len(pages),
            num_chunks=num_added,
            processing_duration_ms=duration_ms,
            embedding_model=embedding_service.get_model_name(),
            status="success"
        )
        event_publisher.publish(event=event, routing_key="document.ingested")
        
        logger.info(
            f"Document ingested successfully: {file.filename} "
            f"({len(pages)} pages, {num_added} chunks, {duration_ms}ms)"
        )
        
        return IngestResponse(
            document_id=document_id,
            filename=file.filename,
            num_pages=len(pages),
            num_chunks=num_added,
            processing_duration_ms=duration_ms,
            status="success"
        )
        
    except Exception as e:
        logger.error(f"Failed to ingest document {file.filename}: {e}", exc_info=True)
        
        # Publish failure event
        duration_ms = int((time.time() - start_time) * 1000)
        event = DocumentIngestedEvent(
            document_id=document_id,
            filename=file.filename,
            num_pages=0,
            num_chunks=0,
            processing_duration_ms=duration_ms,
            embedding_model=embedding_service.get_model_name(),
            status="failed",
            error_message=str(e)
        )
        event_publisher.publish(event=event, routing_key="document.ingested")
        
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/collection/info", response_model=CollectionInfoResponse)
async def get_collection_info():
    """Get information about the vector store collection."""
    try:
        info = vector_store.get_collection_info()
        return CollectionInfoResponse(**info)
    except Exception as e:
        logger.error(f"Failed to get collection info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

