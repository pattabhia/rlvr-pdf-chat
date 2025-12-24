"""
Dataset Writer - Writes training data to JSONL files

Supports multiple formats:
- Standard: Full training data with verification and rewards
- DPO: Direct Preference Optimization format (requires multiple candidates)
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


# Quality filters for DPO pairs
HEDGING_PHRASES = [
    "unfortunately",
    "the provided documents do not mention",
    "the documents do not mention",
    "the context does not mention",
    "i don't see",
    "i'm not sure",
    "i cannot find",
    "there is no information",
    "the provided context does not",
    "based on the provided documents, there is no",
    "i'm happy to help, but",
    "could you please provide more",
]

EVASIVE_PATTERNS = [
    r"unfortunately.*do(?:es)? not mention",
    r"(?:documents?|context) do(?:es)? not (?:mention|provide|contain)",
    r"i (?:don't|do not) see.*in (?:the )?(?:documents?|context)",
    r"there is no (?:information|mention)",
]


class DatasetWriter:
    """
    Writes training data to JSONL files.
    
    Creates monthly files to organize data by time period.
    """
    
    def __init__(self, output_dir: str = "/app/data/training_data"):
        """
        Initialize dataset writer.
        
        Args:
            output_dir: Directory to write JSONL files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Dataset Writer initialized: {self.output_dir}")
    
    def write_entry(self, entry: Dict) -> None:
        """
        Write a complete training data entry to JSONL file.
        
        Args:
            entry: Complete entry with answer, verification, and reward data
        """
        try:
            # Create monthly file
            month_str = datetime.now().strftime("%Y%m")
            output_file = self.output_dir / f"training_data_{month_str}.jsonl"
            
            # Format entry for training
            training_entry = self._format_training_entry(entry)
            
            # Append to JSONL file
            with output_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(training_entry, ensure_ascii=False) + "\n")
            
            logger.info(f"Wrote entry to {output_file.name}: {entry['question'][:50]}...")
            
        except Exception as e:
            logger.error(f"Failed to write entry: {e}", exc_info=True)
    
    def _format_training_entry(self, entry: Dict) -> Dict:
        """
        Format entry for training data.
        
        Args:
            entry: Raw entry from event aggregator
            
        Returns:
            Formatted training entry
        """
        # Extract context strings
        contexts = []
        if "contexts" in entry:
            for ctx in entry["contexts"]:
                if isinstance(ctx, dict):
                    contexts.append(ctx.get("content", ""))
                elif isinstance(ctx, str):
                    contexts.append(ctx)
        
        # Build training entry
        training_entry = {
            "timestamp": entry.get("timestamp", datetime.utcnow().isoformat()),
            "question": entry["question"],
            "answer": entry["answer"],
            "contexts": contexts,
            "verification": entry.get("verification", {}),
            "reward": entry.get("reward", {}),
            "metadata": {
                "answer_event_id": entry.get("answer_event_id"),
                "verification_event_id": entry.get("verification_event_id"),
                "reward_event_id": entry.get("reward_event_id"),
                **entry.get("metadata", {})
            }
        }
        
        return training_entry
    
    def get_stats(self) -> Dict:
        """
        Get statistics about written datasets.
        
        Returns:
            Dictionary with file counts and entry counts
        """
        jsonl_files = list(self.output_dir.glob("training_data_*.jsonl"))
        
        total_entries = 0
        for file in jsonl_files:
            try:
                with file.open("r", encoding="utf-8") as f:
                    total_entries += sum(1 for _ in f)
            except Exception as e:
                logger.warning(f"Failed to count entries in {file}: {e}")
        
        return {
            "output_dir": str(self.output_dir),
            "num_files": len(jsonl_files),
            "total_entries": total_entries,
            "files": [f.name for f in jsonl_files]
        }


class DPODatasetWriter:
    """
    Writes training data in DPO (Direct Preference Optimization) format.

    DPO format requires:
    - prompt: The question with context
    - chosen: The preferred answer (high reward/verification)
    - rejected: The less preferred answer (low reward/verification)

    Automatically groups answers by question and creates DPO pairs.
    """

    def __init__(
        self,
        output_dir: str = "/app/data/dpo_data",
        min_score_diff: float = 0.3,  # Increased from 0.15 to 0.3
        min_chosen_score: float = 0.7,  # New: minimum score for chosen answer
        enable_quality_filter: bool = True  # New: enable behavioral quality checks
    ):
        """
        Initialize DPO dataset writer.

        Args:
            output_dir: Directory to write DPO JSONL files
            min_score_diff: Minimum score difference between chosen/rejected (default: 0.3)
            min_chosen_score: Minimum score for chosen answer (default: 0.7)
            enable_quality_filter: Enable quality checks for chosen answers (default: True)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.min_score_diff = min_score_diff
        self.min_chosen_score = min_chosen_score
        self.enable_quality_filter = enable_quality_filter

        # Store answers by batch_id (for multi-candidate requests)
        self.answers_by_batch: Dict[str, List[Dict]] = defaultdict(list)

        # Also store by question (for backward compatibility)
        self.answers_by_question: Dict[str, List[Dict]] = defaultdict(list)

        # Statistics
        self.stats = {
            "total_pairs_attempted": 0,
            "rejected_low_score_diff": 0,
            "rejected_low_chosen_score": 0,
            "rejected_quality_filter": 0,
            "pairs_created": 0
        }

        logger.info(
            f"DPO Dataset Writer initialized: {self.output_dir} "
            f"(min_score_diff={min_score_diff}, min_chosen_score={min_chosen_score}, "
            f"quality_filter={'enabled' if enable_quality_filter else 'disabled'})"
        )
    
    def add_entry(self, entry: Dict) -> None:
        """
        Add a training entry and automatically create DPO pairs if possible.

        Args:
            entry: Complete training entry with verification scores
        """
        question = entry["question"].strip()
        batch_id = entry.get("batch_id")
        total_candidates = entry.get("total_candidates")

        # Add to answers for this question (backward compatibility)
        self.answers_by_question[question].append(entry)

        # If this is part of a multi-candidate batch, track by batch_id
        if batch_id:
            self.answers_by_batch[batch_id].append(entry)

            # Only try to create DPO pairs when we have all candidates
            if total_candidates and len(self.answers_by_batch[batch_id]) >= total_candidates:
                logger.info(f"All {total_candidates} candidates received for batch {batch_id[:8]}, creating DPO pairs...")
                self._try_create_dpo_pairs_for_batch(batch_id)
        else:
            # Single answer or legacy mode - try immediately
            self._try_create_dpo_pairs(question)

    def _is_hedging_answer(self, answer: str) -> bool:
        """
        Check if answer contains hedging/evasive language.

        Args:
            answer: Answer text to check

        Returns:
            True if answer contains hedging phrases
        """
        answer_lower = answer.lower()

        # Check for hedging phrases
        for phrase in HEDGING_PHRASES:
            if phrase in answer_lower:
                return True

        # Check for evasive patterns
        for pattern in EVASIVE_PATTERNS:
            if re.search(pattern, answer_lower):
                return True

        return False

    def _passes_verbatim_test(self, answer: str) -> bool:
        """
        Apply the "verbatim test": Would we be happy if the model copies this answer verbatim?

        Checks for:
        - Not too short (< 50 chars suggests incomplete answer)
        - Not hedging/evasive
        - Contains actionable content

        Args:
            answer: Answer text to check

        Returns:
            True if answer passes verbatim test
        """
        # Too short
        if len(answer.strip()) < 50:
            return False

        # Contains hedging
        if self._is_hedging_answer(answer):
            return False

        # Check for actionable content (contains at least one of these indicators)
        actionable_indicators = [
            "you can",
            "to ",  # "to reduce", "to optimize", etc.
            "use ",
            "configure",
            "set ",
            "enable",
            "disable",
            "increase",
            "decrease",
            "consider",
            "recommend",
            "best practice",
            "should",
        ]

        answer_lower = answer.lower()
        has_actionable_content = any(indicator in answer_lower for indicator in actionable_indicators)

        return has_actionable_content

    def _get_overall_score(self, entry: Dict) -> float:
        """Extract overall score from entry (verification or reward)."""
        # Try verification score first
        verification = entry.get("verification", {})
        if "overall_score" in verification:
            return verification["overall_score"]

        # Fallback to reward score
        reward = entry.get("reward", {})
        if "score" in reward:
            return reward["score"]

        # Fallback: average of faithfulness and relevancy
        faithfulness = verification.get("faithfulness_score", 0.0)
        relevancy = verification.get("relevancy_score", 0.0)
        if faithfulness > 0 or relevancy > 0:
            return (faithfulness + relevancy) / 2

        return 0.0

    def _try_create_dpo_pairs_for_batch(self, batch_id: str) -> None:
        """
        Try to create DPO pairs for a multi-candidate batch.

        Args:
            batch_id: The batch ID to create pairs for
        """
        answers = self.answers_by_batch[batch_id]

        if not answers:
            logger.warning(f"DPO: No answers found for batch {batch_id[:8]}")
            return

        question = answers[0]["question"]
        logger.info(f"DPO: Processing batch {batch_id[:8]} with {len(answers)} candidates for '{question[:50]}...'")

        # Use the common logic
        self._create_dpo_pairs_from_answers(answers, question, f"batch {batch_id[:8]}")

        # Clean up batch after processing
        del self.answers_by_batch[batch_id]

    def _try_create_dpo_pairs(self, question: str) -> None:
        """
        Try to create DPO pairs for a question if we have multiple answers.

        Applies quality filters to ensure chosen answers represent target production behavior.

        Args:
            question: The question to create pairs for
        """
        answers = self.answers_by_question[question]

        # Need at least 2 answers
        if len(answers) < 2:
            logger.debug(f"DPO: Only {len(answers)} answer(s) for '{question[:50]}...', need 2+")
            return

        # Use the common logic
        self._create_dpo_pairs_from_answers(answers, question, f"question")

    def _create_dpo_pairs_from_answers(self, answers: List[Dict], question: str, source: str) -> None:
        """
        Common logic to create DPO pairs from a list of answers.

        Args:
            answers: List of answer entries
            question: The question
            source: Description of the source (for logging)
        """

        # Score and filter answers
        scored_answers = [
            (entry, self._get_overall_score(entry))
            for entry in answers
            if self._get_overall_score(entry) > 0
        ]

        if len(scored_answers) < 2:
            logger.warning(f"DPO: Only {len(scored_answers)} scored answer(s) for '{question[:50]}...', need 2+")
            return

        # Sort by score (descending)
        scored_answers.sort(key=lambda x: x[1], reverse=True)

        # Get best and worst
        best_entry, best_score = scored_answers[0]
        worst_entry, worst_score = scored_answers[-1]

        self.stats["total_pairs_attempted"] += 1

        # Check minimum score difference
        score_diff = best_score - worst_score
        logger.info(
            f"DPO: {source} '{question[:50]}...' has {len(scored_answers)} answers, "
            f"score diff: {score_diff:.3f} (best={best_score:.3f}, worst={worst_score:.3f})"
        )

        if score_diff < self.min_score_diff:
            logger.debug(
                f"❌ Score diff too small for '{question[:50]}...': "
                f"{score_diff:.3f} < {self.min_score_diff}"
            )
            self.stats["rejected_low_score_diff"] += 1
            return

        # Check minimum chosen score (new quality gate)
        if best_score < self.min_chosen_score:
            logger.info(
                f"❌ Chosen score too low for '{question[:50]}...': "
                f"{best_score:.3f} < {self.min_chosen_score} (not production-ready)"
            )
            self.stats["rejected_low_chosen_score"] += 1
            return

        # Apply verbatim test (new quality gate)
        if self.enable_quality_filter:
            chosen_answer = best_entry["answer"]
            if not self._passes_verbatim_test(chosen_answer):
                logger.info(
                    f"❌ Chosen answer failed verbatim test for '{question[:50]}...': "
                    f"Contains hedging or lacks actionable content"
                )
                logger.debug(f"   Answer preview: {chosen_answer[:150]}...")
                self.stats["rejected_quality_filter"] += 1
                return

        # All quality gates passed - create DPO pair
        logger.info(f"✅ All quality checks passed for '{question[:50]}...'")
        self._write_dpo_pair(best_entry, worst_entry, score_diff)

    def _write_dpo_pair(self, chosen_entry: Dict, rejected_entry: Dict, score_diff: float) -> None:
        """
        Write a DPO training pair.

        Args:
            chosen_entry: Entry with high reward/verification
            rejected_entry: Entry with low reward/verification (same question)
            score_diff: Score difference between chosen and rejected
        """
        try:
            # Create monthly file
            month_str = datetime.now().strftime("%Y%m")
            output_file = self.output_dir / f"dpo_data_{month_str}.jsonl"

            # Build prompt (just the question, context is in the answer)
            question = chosen_entry["question"]

            # Build DPO entry
            dpo_entry = {
                "prompt": question,
                "chosen": chosen_entry["answer"],
                "rejected": rejected_entry["answer"],
                "metadata": {
                    "chosen_score": self._get_overall_score(chosen_entry),
                    "rejected_score": self._get_overall_score(rejected_entry),
                    "score_difference": score_diff,
                    "num_candidates": len(self.answers_by_question[question])
                }
            }

            # Append to JSONL file
            with output_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(dpo_entry, ensure_ascii=False) + "\n")

            self.stats["pairs_created"] += 1

            logger.info(
                f"✅ Created HIGH-QUALITY DPO pair for '{question[:50]}...' "
                f"(Δ={score_diff:.3f}, chosen_score={self._get_overall_score(chosen_entry):.3f})"
            )

            # Log statistics periodically
            if self.stats["pairs_created"] % 10 == 0:
                self._log_statistics()

        except Exception as e:
            logger.error(f"Failed to write DPO pair: {e}", exc_info=True)

    def _log_statistics(self) -> None:
        """Log DPO pair creation statistics."""
        total = self.stats["total_pairs_attempted"]
        if total == 0:
            return

        created = self.stats["pairs_created"]
        acceptance_rate = (created / total) * 100 if total > 0 else 0

        logger.info("=" * 60)
        logger.info("DPO DATASET QUALITY STATISTICS")
        logger.info("=" * 60)
        logger.info(f"Total pairs attempted:        {total}")
        logger.info(f"✅ Pairs created:              {created} ({acceptance_rate:.1f}%)")
        logger.info(f"❌ Rejected (low score diff):  {self.stats['rejected_low_score_diff']}")
        logger.info(f"❌ Rejected (low chosen score): {self.stats['rejected_low_chosen_score']}")
        logger.info(f"❌ Rejected (quality filter):  {self.stats['rejected_quality_filter']}")
        logger.info("=" * 60)

    def get_statistics(self) -> Dict:
        """Get DPO pair creation statistics."""
        total = self.stats["total_pairs_attempted"]
        created = self.stats["pairs_created"]
        acceptance_rate = (created / total) * 100 if total > 0 else 0

        return {
            **self.stats,
            "acceptance_rate": acceptance_rate
        }

