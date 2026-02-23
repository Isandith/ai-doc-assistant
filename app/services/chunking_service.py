from typing import List, Dict
import re


class ChunkingService:
    """Service for splitting text into chunks with token estimation"""
    
    @staticmethod
    def estimate_tokens(text: str) -> int:
        """
        Rough token estimation (1 token ~= 4 characters for English text)
        For more accurate counting, use tiktoken library
        """
        return len(text) // 4
    
    @staticmethod
    def chunk_text(text: str, max_tokens: int = 500, overlap_tokens: int = 50) -> List[Dict[str, any]]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Input text to chunk
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Number of overlapping tokens between chunks
            
        Returns:
            List of dictionaries with chunk_index, text, and token_count
        """
        if not text or not text.strip():
            return []
        
        # Convert tokens to approximate characters
        max_chars = max_tokens * 4
        overlap_chars = overlap_tokens * 4
        
        # Split by sentences first (simple approach)
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        chunk_index = 0
        
        for sentence in sentences:
            # If adding this sentence exceeds max, save current chunk
            if len(current_chunk) + len(sentence) > max_chars and current_chunk:
                chunks.append({
                    "chunk_index": chunk_index,
                    "text": current_chunk.strip(),
                    "token_count": ChunkingService.estimate_tokens(current_chunk)
                })
                
                # Start new chunk with overlap (last part of previous chunk)
                if overlap_chars > 0 and len(current_chunk) > overlap_chars:
                    current_chunk = current_chunk[-overlap_chars:] + " " + sentence
                else:
                    current_chunk = sentence
                
                chunk_index += 1
            else:
                current_chunk += " " + sentence if current_chunk else sentence
        
        # Add the last chunk
        if current_chunk.strip():
            chunks.append({
                "chunk_index": chunk_index,
                "text": current_chunk.strip(),
                "token_count": ChunkingService.estimate_tokens(current_chunk)
            })
        
        return chunks
    
    @staticmethod
    def chunk_pages(pages: List[Dict[str, any]], max_tokens: int = 500, overlap_tokens: int = 50) -> List[Dict[str, any]]:
        """
        Chunk multiple pages while preserving page numbers.
        
        Args:
            pages: List of page dictionaries with page_number and text
            max_tokens: Maximum tokens per chunk
            overlap_tokens: Overlap between chunks
            
        Returns:
            List of chunk dictionaries with page_number, chunk_index, text, and token_count
        """
        all_chunks = []
        
        for page in pages:
            page_number = page["page_number"]
            page_text = page["text"]
            
            # Chunk the page text
            page_chunks = ChunkingService.chunk_text(page_text, max_tokens, overlap_tokens)
            
            # Add page number to each chunk
            for chunk in page_chunks:
                all_chunks.append({
                    "page_number": page_number,
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "token_count": chunk["token_count"]
                })
        
        return all_chunks
