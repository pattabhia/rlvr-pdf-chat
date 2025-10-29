"""
Dataset Manager - Manages training data JSONL files

Provides functionality for:
- Reading/writing JSONL files
- Computing statistics
- Filtering entries
- Exporting to different formats
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Iterator
from datetime import datetime
from collections import defaultdict

from src.models import (
    TrainingDataEntry,
    TrainingDataEntryResponse,
    DatasetStats,
    DPOEntry,
    ExportRequest
)

logger = logging.getLogger(__name__)


class DatasetManager:
    """
    Manages training data JSONL files.
    
    Handles reading, writing, filtering, and exporting training datasets.
    """
    
    def __init__(self, data_dir: str = "/app/data/training_data"):
        """
        Initialize dataset manager.
        
        Args:
            data_dir: Directory containing training data JSONL files
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Dataset Manager initialized: {self.data_dir}")
    
    def list_datasets(self) -> List[str]:
        """
        List all dataset files.
        
        Returns:
            List of dataset file names
        """
        jsonl_files = sorted(self.data_dir.glob("training_data_*.jsonl"))
        return [f.name for f in jsonl_files]
    
    def get_dataset_stats(self, file_name: str) -> DatasetStats:
        """
        Get statistics for a dataset file.
        
        Args:
            file_name: Dataset file name
            
        Returns:
            Dataset statistics
        """
        file_path = self.data_dir / file_name
        
        if not file_path.exists():
            raise FileNotFoundError(f"Dataset file not found: {file_name}")
        
        # Read all entries and compute stats
        entries = list(self._read_entries(file_name))
        
        if not entries:
            return DatasetStats(
                file_name=file_name,
                num_entries=0,
                date_range={"earliest": None, "latest": None},
                avg_verification_score=0.0,
                avg_reward_score=0.0,
                domains=[],
                file_size_bytes=file_path.stat().st_size
            )
        
        # Extract timestamps
        timestamps = [e.timestamp for e in entries]
        earliest = min(timestamps)
        latest = max(timestamps)
        
        # Compute averages
        verification_scores = [e.verification.overall_score for e in entries]
        reward_scores = [e.reward.score for e in entries]
        avg_verification = sum(verification_scores) / len(verification_scores)
        avg_reward = sum(reward_scores) / len(reward_scores)
        
        # Extract unique domains
        domains = list(set(e.reward.domain for e in entries))
        
        return DatasetStats(
            file_name=file_name,
            num_entries=len(entries),
            date_range={"earliest": earliest, "latest": latest},
            avg_verification_score=round(avg_verification, 3),
            avg_reward_score=round(avg_reward, 3),
            domains=sorted(domains),
            file_size_bytes=file_path.stat().st_size
        )
    
    def get_all_stats(self) -> Dict:
        """
        Get statistics for all datasets.
        
        Returns:
            Dictionary with overall statistics
        """
        datasets = self.list_datasets()
        
        total_entries = 0
        all_stats = []
        
        for file_name in datasets:
            try:
                stats = self.get_dataset_stats(file_name)
                all_stats.append(stats)
                total_entries += stats.num_entries
            except Exception as e:
                logger.error(f"Failed to get stats for {file_name}: {e}")
        
        return {
            "datasets": all_stats,
            "total_datasets": len(datasets),
            "total_entries": total_entries
        }
    
    def _read_entries(self, file_name: str) -> Iterator[TrainingDataEntry]:
        """
        Read entries from a JSONL file.
        
        Args:
            file_name: Dataset file name
            
        Yields:
            Training data entries
        """
        file_path = self.data_dir / file_name
        
        with file_path.open("r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                try:
                    data = json.loads(line.strip())
                    entry = TrainingDataEntry(**data)
                    yield entry
                except Exception as e:
                    logger.warning(f"Failed to parse line {line_no} in {file_name}: {e}")
    
    def get_entries(
        self,
        file_name: Optional[str] = None,
        min_verification_score: Optional[float] = None,
        min_reward_score: Optional[float] = None,
        domains: Optional[List[str]] = None,
        limit: Optional[int] = None,
        offset: int = 0
    ) -> List[TrainingDataEntryResponse]:
        """
        Get entries with optional filtering.
        
        Args:
            file_name: Specific file to read (if None, read all files)
            min_verification_score: Minimum verification score
            min_reward_score: Minimum reward score
            domains: Filter by domains
            limit: Maximum number of entries to return
            offset: Number of entries to skip
            
        Returns:
            List of training data entries
        """
        # Determine which files to read
        if file_name:
            files = [file_name]
        else:
            files = self.list_datasets()
        
        # Read and filter entries
        results = []
        skipped = 0
        
        for fname in files:
            try:
                for entry in self._read_entries(fname):
                    # Apply filters
                    if min_verification_score and entry.verification.overall_score < min_verification_score:
                        continue
                    if min_reward_score and entry.reward.score < min_reward_score:
                        continue
                    if domains and entry.reward.domain not in domains:
                        continue
                    
                    # Apply offset
                    if skipped < offset:
                        skipped += 1
                        continue
                    
                    # Add to results
                    results.append(TrainingDataEntryResponse(
                        **entry.dict(),
                        entry_id=f"{fname}:{len(results)}",
                        file_name=fname
                    ))
                    
                    # Check limit
                    if limit and len(results) >= limit:
                        return results
                        
            except Exception as e:
                logger.error(f"Failed to read entries from {fname}: {e}")

        return results

    def export_to_dpo(self, export_request: ExportRequest) -> str:
        """
        Export dataset to DPO format.

        DPO requires pairs of (chosen, rejected) answers for the same question.
        Since we don't have multiple candidates per question yet, we'll create
        pairs by treating high-reward answers as "chosen" and low-reward as "rejected".

        Args:
            export_request: Export configuration

        Returns:
            Path to exported file
        """
        # Get entries with filters
        entries = self.get_entries(
            file_name=export_request.file_name,
            min_verification_score=export_request.min_verification_score,
            min_reward_score=export_request.min_reward_score,
            domains=export_request.domains
        )

        # Group by question to find pairs
        question_groups = defaultdict(list)
        for entry in entries:
            question_groups[entry.question].append(entry)

        # Create DPO pairs
        dpo_entries = []
        for question, group in question_groups.items():
            if len(group) < 2:
                continue

            # Sort by reward score
            sorted_group = sorted(group, key=lambda e: e.reward.score, reverse=True)
            chosen = sorted_group[0]
            rejected = sorted_group[-1]

            # Skip if no clear preference
            if chosen.reward.score <= rejected.reward.score:
                continue

            # Build prompt with context
            context_str = "\n\n".join(chosen.contexts[:3]) if chosen.contexts else ""
            prompt = f"Context:\n{context_str}\n\nQuestion: {question}\n\nAnswer:"

            dpo_entry = DPOEntry(
                prompt=prompt,
                chosen=chosen.answer,
                rejected=rejected.answer,
                metadata={
                    "chosen_reward": chosen.reward.score,
                    "rejected_reward": rejected.reward.score,
                    "chosen_verification": chosen.verification.overall_score,
                    "rejected_verification": rejected.verification.overall_score,
                    "domain": chosen.reward.domain
                }
            )
            dpo_entries.append(dpo_entry)

        # Write to file
        export_file = self.data_dir / f"dpo_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        with export_file.open("w", encoding="utf-8") as f:
            for entry in dpo_entries:
                f.write(json.dumps(entry.dict(), ensure_ascii=False) + "\n")

        logger.info(f"Exported {len(dpo_entries)} DPO pairs to {export_file.name}")
        return str(export_file)

    def export_to_sft(self, export_request: ExportRequest) -> str:
        """
        Export dataset to SFT (Supervised Fine-Tuning) format.

        SFT format is simple: prompt + completion pairs.

        Args:
            export_request: Export configuration

        Returns:
            Path to exported file
        """
        # Get entries with filters
        entries = self.get_entries(
            file_name=export_request.file_name,
            min_verification_score=export_request.min_verification_score,
            min_reward_score=export_request.min_reward_score,
            domains=export_request.domains
        )

        # Create SFT entries
        sft_entries = []
        for entry in entries:
            # Build prompt with context
            context_str = "\n\n".join(entry.contexts[:3]) if entry.contexts else ""
            prompt = f"Context:\n{context_str}\n\nQuestion: {entry.question}\n\nAnswer:"

            sft_entry = {
                "prompt": prompt,
                "completion": entry.answer,
                "metadata": {
                    "verification_score": entry.verification.overall_score,
                    "reward_score": entry.reward.score,
                    "domain": entry.reward.domain
                }
            }
            sft_entries.append(sft_entry)

        # Write to file
        export_file = self.data_dir / f"sft_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        with export_file.open("w", encoding="utf-8") as f:
            for entry in sft_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        logger.info(f"Exported {len(sft_entries)} SFT entries to {export_file.name}")
        return str(export_file)

    def export_to_jsonl(self, export_request: ExportRequest) -> str:
        """
        Export dataset to standard JSONL format (filtered).

        Args:
            export_request: Export configuration

        Returns:
            Path to exported file
        """
        # Get entries with filters
        entries = self.get_entries(
            file_name=export_request.file_name,
            min_verification_score=export_request.min_verification_score,
            min_reward_score=export_request.min_reward_score,
            domains=export_request.domains
        )

        # Write to file
        export_file = self.data_dir / f"filtered_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
        with export_file.open("w", encoding="utf-8") as f:
            for entry in entries:
                # Remove entry_id and file_name (added by get_entries)
                entry_dict = entry.dict()
                entry_dict.pop("entry_id", None)
                entry_dict.pop("file_name", None)
                f.write(json.dumps(entry_dict, ensure_ascii=False) + "\n")

        logger.info(f"Exported {len(entries)} entries to {export_file.name}")
        return str(export_file)

