#!/usr/bin/env python3
"""
DPO Dataset Preparation Script

Converts RLVR training data (JSONL with RAGAS scores) into DPO-compatible format.

Process:
1. Load all training data entries
2. Group by question (find multiple answers per question)
3. Rank by RAGAS overall_score
4. Create chosen/rejected pairs (highest vs lowest score)
5. Output DPO format: {prompt, chosen, rejected}

Usage:
    python scripts/prepare_dpo_dataset.py \
        --input data/training_data/training_data_202512.jsonl \
        --output data/dpo_dataset/dpo_training_data.jsonl \
        --min-score-diff 0.2
"""

import json
import argparse
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_training_data(input_path: Path) -> List[Dict[str, Any]]:
    """Load training data from JSONL file (handles both single-line and multi-line JSON)."""
    entries = []

    # Try to load as multi-line JSON first (pretty-printed)
    try:
        with open(input_path, 'r') as f:
            content = f.read()

        # Split by lines starting with '{'
        import re
        json_objects = re.split(r'\n(?=\{)', content)

        for obj_str in json_objects:
            obj_str = obj_str.strip()
            if not obj_str:
                continue
            try:
                entry = json.loads(obj_str)
                if isinstance(entry, dict):
                    entries.append(entry)
            except json.JSONDecodeError:
                continue

    except Exception as e:
        logger.error(f"Failed to load training data: {e}")
        return []

    logger.info(f"Loaded {len(entries)} training entries from {input_path}")
    return entries


def group_by_question(entries: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group entries by question."""
    grouped = defaultdict(list)
    
    for entry in entries:
        question = entry.get('question', '').strip()
        if question:
            grouped[question].append(entry)
    
    logger.info(f"Grouped into {len(grouped)} unique questions")
    
    # Log statistics
    multi_answer_questions = {q: answers for q, answers in grouped.items() if len(answers) > 1}
    logger.info(f"Questions with multiple answers: {len(multi_answer_questions)}")
    
    for question, answers in sorted(multi_answer_questions.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
        logger.info(f"  '{question[:60]}...' has {len(answers)} answers")
    
    return grouped


def get_overall_score(entry: Dict[str, Any]) -> float:
    """Extract overall score from entry."""
    verification = entry.get('verification', {})
    
    # Try overall_score first
    if 'overall_score' in verification:
        return verification['overall_score']
    
    # Fallback: average of faithfulness and relevancy
    faithfulness = verification.get('faithfulness_score', 0.0)
    relevancy = verification.get('relevancy_score', 0.0)
    
    if faithfulness > 0 or relevancy > 0:
        return (faithfulness + relevancy) / 2
    
    return 0.0


def create_dpo_pairs(
    grouped: Dict[str, List[Dict[str, Any]]],
    min_score_diff: float = 0.2
) -> List[Dict[str, str]]:
    """
    Create DPO training pairs (prompt, chosen, rejected).
    
    Args:
        grouped: Questions grouped by text
        min_score_diff: Minimum score difference between chosen and rejected
        
    Returns:
        List of DPO training examples
    """
    dpo_pairs = []
    
    for question, answers in grouped.items():
        # Need at least 2 answers to create a pair
        if len(answers) < 2:
            continue
        
        # Filter out answers without verification scores
        scored_answers = [
            (entry, get_overall_score(entry))
            for entry in answers
            if get_overall_score(entry) > 0
        ]
        
        if len(scored_answers) < 2:
            continue
        
        # Sort by score (descending)
        scored_answers.sort(key=lambda x: x[1], reverse=True)
        
        # Get highest and lowest scoring answers
        best_entry, best_score = scored_answers[0]
        worst_entry, worst_score = scored_answers[-1]
        
        # Check minimum score difference
        score_diff = best_score - worst_score
        if score_diff < min_score_diff:
            logger.debug(f"Skipping '{question[:40]}...' - score diff too small: {score_diff:.3f}")
            continue
        
        # Create DPO pair
        dpo_pair = {
            "prompt": question,
            "chosen": best_entry.get('answer', ''),
            "rejected": worst_entry.get('answer', ''),
            "metadata": {
                "chosen_score": best_score,
                "rejected_score": worst_score,
                "score_difference": score_diff,
                "num_candidates": len(scored_answers),
                "chosen_verification": best_entry.get('verification', {}),
                "rejected_verification": worst_entry.get('verification', {})
            }
        }
        
        dpo_pairs.append(dpo_pair)
        
        logger.debug(
            f"Created pair for '{question[:40]}...' - "
            f"chosen: {best_score:.3f}, rejected: {worst_score:.3f}, diff: {score_diff:.3f}"
        )
    
    logger.info(f"Created {len(dpo_pairs)} DPO training pairs")
    return dpo_pairs


def save_dpo_dataset(dpo_pairs: List[Dict[str, str]], output_path: Path):
    """Save DPO dataset to JSONL file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        for pair in dpo_pairs:
            f.write(json.dumps(pair) + '\n')
    
    logger.info(f"Saved {len(dpo_pairs)} DPO pairs to {output_path}")


def main():
    parser = argparse.ArgumentParser(description='Prepare DPO dataset from RLVR training data')
    parser.add_argument(
        '--input',
        type=Path,
        default=Path('data/training_data/training_data_202512.jsonl'),
        help='Input JSONL file with RLVR training data'
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('data/dpo_dataset/dpo_training_data.jsonl'),
        help='Output JSONL file for DPO training'
    )
    parser.add_argument(
        '--min-score-diff',
        type=float,
        default=0.2,
        help='Minimum score difference between chosen and rejected (default: 0.2)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logger.setLevel(logging.DEBUG)
    
    # Load training data
    entries = load_training_data(args.input)
    
    if not entries:
        logger.error("No training data found!")
        return
    
    # Group by question
    grouped = group_by_question(entries)
    
    # Create DPO pairs
    dpo_pairs = create_dpo_pairs(grouped, min_score_diff=args.min_score_diff)
    
    if not dpo_pairs:
        logger.warning("No DPO pairs created! Try lowering --min-score-diff")
        return
    
    # Save dataset
    save_dpo_dataset(dpo_pairs, args.output)
    
    # Print statistics
    print("\n" + "="*60)
    print("DPO Dataset Statistics")
    print("="*60)
    print(f"Total training entries: {len(entries)}")
    print(f"Unique questions: {len(grouped)}")
    print(f"DPO pairs created: {len(dpo_pairs)}")
    print(f"Output file: {args.output}")
    print("="*60)


if __name__ == "__main__":
    main()

