"""
QA Service - Core RAG Logic

Simplified RAG service for microservices architecture.
Focuses on question answering without RLVR complexity (handled by workers).
"""

from typing import List, Dict, Any, Optional
from string import Template
import logging

from langchain_community.embeddings import SentenceTransformerEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

from .llm_port import LLMPort

logger = logging.getLogger(__name__)


QA_PROMPT = Template(
    "You are an expert AWS cloud architect assistant. Your goal is to provide clear, actionable guidance.\n\n"
    "Context from documentation:\n${context}\n\n"
    "Question: ${question}\n\n"
    "Instructions:\n"
    "1. Provide a direct, helpful answer based on the context above\n"
    "2. If the context contains relevant information, use it to give specific guidance\n"
    "3. If the context is incomplete, combine what's available with general AWS best practices\n"
    "4. Focus on actionable recommendations rather than disclaimers\n"
    "5. Avoid phrases like 'the documents do not mention' or 'unfortunately' - instead, provide what you know\n"
    "6. Be concise but thorough\n\n"
    "Answer:"
)


class QAService:
    """
    Simplified QA Service for microservices architecture.
    
    Responsibilities:
    - Retrieve relevant context from vector store
    - Generate answer using LLM
    - Return answer with context and metadata
    
    Does NOT handle:
    - RLVR (handled by Reward Computation Worker)
    - Verification (handled by Verification Worker)
    - Training data logging (handled by Dataset Generation Worker)
    """
    
    def __init__(
        self,
        qdrant_url: str,
        qdrant_collection: str,
        llm: LLMPort,
        embedding_model: str = "all-MiniLM-L6-v2",
        top_k: int = 5,
        candidate_temperatures: List[float] = None
    ):
        """
        Initialize QA Service.

        Args:
            qdrant_url: Qdrant server URL
            qdrant_collection: Collection name
            llm: LLM adapter (implements LLMPort)
            embedding_model: Sentence transformer model
            top_k: Number of documents to retrieve
            candidate_temperatures: List of temperatures for multi-candidate generation
        """
        self.qdrant_url = qdrant_url
        self.qdrant_collection = qdrant_collection
        self.llm = llm
        self.top_k = top_k

        # Default temperatures for diversity: low (deterministic), medium, high (creative)
        self.candidate_temperatures = candidate_temperatures or [0.3, 0.7, 0.9]

        # Initialize components
        logger.info(f"Initializing QA Service...")
        logger.info(f"  Qdrant: {qdrant_url}, collection: {qdrant_collection}")
        logger.info(f"  LLM: {llm.get_model_name()}")
        logger.info(f"  Embedding model: {embedding_model}")
        logger.info(f"  Top-K: {top_k}")
        logger.info(f"  Candidate Temperatures: {self.candidate_temperatures}")

        # Initialize Qdrant client
        self.qdrant_client = QdrantClient(url=qdrant_url)

        # Initialize embeddings
        self.embeddings = SentenceTransformerEmbeddings(model_name=embedding_model)

        logger.info("QA Service initialized successfully")
    
    def retrieve_context(self, question: str) -> List[Dict[str, Any]]:
        """
        Retrieve relevant context from vector store.
        
        Args:
            question: User's question
            
        Returns:
            List of context documents with metadata
        """
        logger.info(f"Retrieving context for question: {question}")
        
        # Generate query embedding
        query_embedding = self.embeddings.embed_query(question)
        
        # Search Qdrant
        search_result = self.qdrant_client.query_points(
            collection_name=self.qdrant_collection,
            query=query_embedding,
            limit=self.top_k,
            with_payload=True,
            with_vectors=False
        )
        
        # Extract documents
        contexts = []
        for point in search_result.points:
            contexts.append({
                "content": point.payload.get("page_content", ""),
                "metadata": point.payload.get("metadata", {}),
                "score": point.score
            })
        
        logger.info(f"Retrieved {len(contexts)} context documents")
        return contexts
    
    def generate_answer(self, question: str, contexts: List[Dict[str, Any]], temperature: Optional[float] = None) -> str:
        """
        Generate answer using LLM.

        Args:
            question: User's question
            contexts: Retrieved context documents
            temperature: Optional temperature override for this generation

        Returns:
            Generated answer
        """
        logger.info(f"Generating answer for question: {question} (temperature={temperature})")

        # Combine contexts
        context_text = "\n\n".join([
            f"[Document {i+1}] {ctx['content']}"
            for i, ctx in enumerate(contexts)
        ])

        # Generate prompt
        prompt = QA_PROMPT.substitute(context=context_text, question=question)

        # Generate answer using LLM port with temperature override
        answer = self.llm.invoke(prompt, temperature=temperature)

        logger.info(f"Generated answer: {answer[:100]}...")
        return answer

    def generate_multiple_candidates(self, question: str, num_candidates: int = 3) -> List[Dict[str, Any]]:
        """
        Generate multiple candidate answers for DPO training.

        This method generates multiple diverse answers for the same question
        by using different sampling strategies (temperature variations).

        Args:
            question: User's question
            num_candidates: Number of candidate answers to generate (default: 3)

        Returns:
            List of candidate answers with contexts and metadata
        """
        logger.info(f"Generating {num_candidates} candidate answers for question: {question}")

        # Retrieve context once (same context for all candidates)
        contexts = self.retrieve_context(question)

        candidates = []
        for i in range(num_candidates):
            # Use different temperature for each candidate to create diversity
            # Cycle through available temperatures if num_candidates > len(temperatures)
            temperature = self.candidate_temperatures[i % len(self.candidate_temperatures)]

            # Generate answer with specific temperature
            answer = self.generate_answer(question, contexts, temperature=temperature)

            candidates.append({
                "question": question,
                "answer": answer,
                "contexts": contexts,
                "metadata": {
                    "top_k": self.top_k,
                    "model": self.llm.get_model_name(),
                    "num_contexts": len(contexts),
                    "candidate_index": i,
                    "temperature": temperature
                }
            })

            logger.info(f"Generated candidate {i+1}/{num_candidates} (temp={temperature}): {answer[:80]}...")

        logger.info(f"Generated {len(candidates)} candidate answers")
        return candidates
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using RAG.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with answer, contexts, and metadata
        """
        # Retrieve context
        contexts = self.retrieve_context(question)
        
        # Generate answer
        answer = self.generate_answer(question, contexts)
        
        return {
            "question": question,
            "answer": answer,
            "contexts": contexts,
            "metadata": {
                "top_k": self.top_k,
                "model": self.llm.get_model_name(),
                "num_contexts": len(contexts)
            }
        }

