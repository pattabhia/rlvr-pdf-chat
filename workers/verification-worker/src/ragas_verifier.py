"""
RAGAS Verifier - Answer quality verification using RAGAS framework

Evaluates RAG answers using:
- Faithfulness: Is the answer grounded in the context?
- Answer Relevancy: Does the answer address the question?
"""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

try:
    from ragas import evaluate
    from ragas.metrics import answer_relevancy, faithfulness
    from datasets import Dataset
    from langchain_ollama import ChatOllama
    from langchain_huggingface import HuggingFaceEmbeddings
    RAGAS_AVAILABLE = True
except Exception as e:
    logger.warning(f"RAGAS dependencies not available: {e}")
    evaluate = None
    answer_relevancy = None
    faithfulness = None
    Dataset = None
    ChatOllama = None
    HuggingFaceEmbeddings = None
    RAGAS_AVAILABLE = False


class RagasVerifier:
    """
    RAGAS verification for answer quality assessment.
    
    Supports two modes:
    1. 'ollama' - LLM-based evaluation using Ollama (accurate but slower)
    2. 'heuristic' - Rule-based evaluation (fast but less accurate)
    """
    
    def __init__(
        self,
        mode: str = "ollama",
        ollama_url: str = "http://ollama:11434",
        ollama_model: str = "llama3.2:3b",
        faithfulness_threshold: float = 0.7,
        relevancy_threshold: float = 0.7
    ):
        """
        Initialize RAGAS verifier.
        
        Args:
            mode: 'ollama' or 'heuristic'
            ollama_url: Ollama server URL (for ollama mode)
            ollama_model: Model name (for ollama mode)
            faithfulness_threshold: Threshold for high confidence
            relevancy_threshold: Threshold for high confidence
        """
        self.mode = mode.lower()
        self.ollama_url = ollama_url
        self.ollama_model = ollama_model
        self.faithfulness_threshold = faithfulness_threshold
        self.relevancy_threshold = relevancy_threshold
        
        logger.info(f"Initialized RAGAS Verifier (mode={self.mode})")
        
        if self.mode == "ollama" and not RAGAS_AVAILABLE:
            logger.warning("RAGAS not available, falling back to heuristic mode")
            self.mode = "heuristic"
    
    def verify(self, question: str, answer: str, contexts: List[str]) -> Dict:
        """
        Verify answer quality.
        
        Args:
            question: User's question
            answer: Generated answer
            contexts: List of context strings
            
        Returns:
            Dictionary with:
            - faithfulness: Score 0-1
            - relevancy: Score 0-1
            - overall_score: Average score
            - confidence: "high" or "low"
            - issues: List of issues
            - mode: Verification mode used
        """
        if self.mode == "ollama" and RAGAS_AVAILABLE:
            try:
                faith, relevancy = self._ragas_verification(question, answer, contexts)
            except Exception as e:
                logger.warning(f"RAGAS verification failed: {e}, using heuristic fallback")
                faith, relevancy = self._heuristic_verification(answer, contexts)
        else:
            faith, relevancy = self._heuristic_verification(answer, contexts)
        
        overall = (faith + relevancy) / 2 if (faith or relevancy) else 0.0
        confidence = (
            "high"
            if faith >= self.faithfulness_threshold and relevancy >= self.relevancy_threshold
            else "low"
        )
        
        return {
            "faithfulness": faith,
            "relevancy": relevancy,
            "overall_score": overall,
            "confidence": confidence,
            "issues": [] if confidence == "high" else ["Low verification confidence"],
            "mode": self.mode
        }
    
    def _ragas_verification(self, question: str, answer: str, contexts: List[str]) -> tuple:
        """
        RAGAS verification using Ollama LLM.

        Returns:
            Tuple of (faithfulness, relevancy)
        """
        logger.info("Running RAGAS verification with Ollama")

        # Create Ollama LLM
        # WORKAROUND: RAGAS 0.2.x has a bug where it passes 'temperature' to AsyncClient.chat()
        # which doesn't accept it. We need to use sync mode or patch the client.
        # For now, we'll catch the error and use fallback scores.
        llm = ChatOllama(
            base_url=self.ollama_url,
            model=self.ollama_model,
            temperature=0.0  # Set default temperature
        )

        # Create local embeddings (same as used in QA service)
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

        # Prepare dataset
        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        }
        dataset = Dataset.from_dict(data)

        # Run RAGAS evaluation with local embeddings
        # RAGAS will handle temperature internally
        results = evaluate(
            dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=llm,
            embeddings=embeddings
        )
        
        # Extract scores
        scores = results.to_pandas().iloc[0]
        faith = float(scores.get("faithfulness", 0.0))
        relevancy = float(scores.get("answer_relevancy", 0.0))
        
        logger.info(f"RAGAS scores: faithfulness={faith:.3f}, relevancy={relevancy:.3f}")
        
        return faith, relevancy
    
    def _heuristic_verification(self, answer: str, contexts: List[str]) -> tuple:
        """
        Heuristic verification (fast, rule-based).

        Uses basic text analysis with variation:
        - Faithfulness: Word overlap between answer and context
        - Relevancy: Answer length, quality indicators, and specificity
        - Adds variation based on answer characteristics

        Returns:
            Tuple of (faithfulness, relevancy)
        """
        logger.debug("Running heuristic verification")

        # Check if answer is substantial
        answer_lower = answer.lower()
        answer_len = len(answer)
        has_substantial_answer = answer_len > 20 and "don't know" not in answer_lower

        # Check context overlap
        context_text = " ".join(contexts).lower()
        answer_words = set(answer_lower.split())
        context_words = set(context_text.split())

        if answer_words:
            overlap_ratio = len(answer_words & context_words) / len(answer_words)
        else:
            overlap_ratio = 0.0

        # Calculate faithfulness based on context overlap
        # Higher overlap = more faithful to context
        if overlap_ratio > 0.5:
            faithfulness = 0.85 + (overlap_ratio - 0.5) * 0.3  # 0.85-1.0
        elif overlap_ratio > 0.3:
            faithfulness = 0.65 + (overlap_ratio - 0.3) * 1.0  # 0.65-0.85
        else:
            faithfulness = 0.40 + overlap_ratio * 0.83  # 0.40-0.65

        # Calculate relevancy based on multiple factors
        base_relevancy = 0.5

        # Factor 1: Answer length (longer = more detailed)
        if answer_len > 200:
            length_bonus = 0.25
        elif answer_len > 100:
            length_bonus = 0.15
        elif answer_len > 50:
            length_bonus = 0.10
        else:
            length_bonus = 0.0

        # Factor 2: Quality indicators
        quality_bonus = 0.0
        quality_indicators = [
            "according to", "document", "specifically", "includes",
            "provides", "describes", "explains", "details"
        ]
        for indicator in quality_indicators:
            if indicator in answer_lower:
                quality_bonus += 0.03
        quality_bonus = min(quality_bonus, 0.15)  # Cap at 0.15

        # Factor 3: Negative indicators
        negative_penalty = 0.0
        if "not explicitly" in answer_lower or "not mentioned" in answer_lower:
            negative_penalty = 0.15
        elif "don't know" in answer_lower or "cannot" in answer_lower:
            negative_penalty = 0.30

        # Factor 4: Specificity (presence of numbers, technical terms)
        specificity_bonus = 0.0
        if any(char.isdigit() for char in answer):
            specificity_bonus += 0.05
        if len([w for w in answer_words if len(w) > 8]) > 3:  # Technical terms
            specificity_bonus += 0.05

        # Calculate final relevancy
        relevancy = base_relevancy + length_bonus + quality_bonus + specificity_bonus - negative_penalty
        relevancy = max(0.3, min(1.0, relevancy))  # Clamp between 0.3 and 1.0

        # Ensure faithfulness is also clamped
        faithfulness = max(0.3, min(1.0, faithfulness))

        logger.debug(f"Heuristic scores: faithfulness={faithfulness:.3f}, relevancy={relevancy:.3f} "
                    f"(overlap={overlap_ratio:.2f}, len={answer_len}, quality={quality_bonus:.2f})")

        return faithfulness, relevancy

