"""
Text Chunker - Split text into chunks with overlap

Uses recursive character splitting for better semantic coherence.
"""

import logging
from typing import List, Dict

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter
except ImportError:
    from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Text chunking using recursive character splitting.
    
    Splits text into chunks while preserving semantic boundaries.
    Uses overlap to maintain context across chunks.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None
    ):
        """
        Initialize text chunker.
        
        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of overlapping characters between chunks
            separators: List of separators to use (in priority order)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Default separators: paragraph > sentence > word > character
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]
        
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
        )
        
        logger.info(
            f"Text Chunker initialized (size={chunk_size}, overlap={chunk_overlap})"
        )
    
    def chunk_pages(
        self,
        pages: List[Dict],
        source_name: str
    ) -> List[Dict]:
        """
        Chunk pages into smaller text segments.
        
        Args:
            pages: List of page dictionaries from PDF processor
            source_name: Name of the source document
            
        Returns:
            List of chunk dictionaries with text and metadata
            
        Example:
            [
                {
                    "text": "Chunk 1 content...",
                    "metadata": {
                        "source": "document.pdf",
                        "page": 1,
                        "chunk_index": 0
                    }
                },
                ...
            ]
        """
        all_chunks = []
        chunk_index = 0
        
        for page in pages:
            page_num = page["page"]
            page_text = page["text"]
            
            if not page_text.strip():
                logger.debug(f"Skipping empty page {page_num}")
                continue
            
            # Split page text into chunks
            text_chunks = self.splitter.split_text(page_text)
            
            # Create chunk dictionaries with metadata
            for chunk_text in text_chunks:
                if not chunk_text.strip():
                    continue
                
                all_chunks.append({
                    "text": chunk_text,
                    "metadata": {
                        "source": source_name,
                        "page": page_num,
                        "chunk_index": chunk_index,
                        "char_count": len(chunk_text)
                    }
                })
                
                chunk_index += 1
        
        logger.info(
            f"Created {len(all_chunks)} chunks from {len(pages)} pages "
            f"(source={source_name})"
        )
        
        return all_chunks
    
    def chunk_text(
        self,
        text: str,
        metadata: Dict = None
    ) -> List[Dict]:
        """
        Chunk a single text string.
        
        Args:
            text: Text to chunk
            metadata: Optional metadata to attach to chunks
            
        Returns:
            List of chunk dictionaries
        """
        if not text.strip():
            return []
        
        metadata = metadata or {}
        chunks = []
        
        text_chunks = self.splitter.split_text(text)
        
        for idx, chunk_text in enumerate(text_chunks):
            if not chunk_text.strip():
                continue
            
            chunks.append({
                "text": chunk_text,
                "metadata": {
                    **metadata,
                    "chunk_index": idx,
                    "char_count": len(chunk_text)
                }
            })
        
        logger.info(f"Created {len(chunks)} chunks from text")
        
        return chunks
    
    def get_stats(self, chunks: List[Dict]) -> Dict:
        """
        Get statistics about chunks.
        
        Args:
            chunks: List of chunk dictionaries
            
        Returns:
            Dictionary with statistics
        """
        if not chunks:
            return {
                "num_chunks": 0,
                "total_chars": 0,
                "avg_chunk_size": 0,
                "min_chunk_size": 0,
                "max_chunk_size": 0
            }
        
        char_counts = [c["metadata"]["char_count"] for c in chunks]
        
        return {
            "num_chunks": len(chunks),
            "total_chars": sum(char_counts),
            "avg_chunk_size": sum(char_counts) // len(char_counts),
            "min_chunk_size": min(char_counts),
            "max_chunk_size": max(char_counts)
        }

