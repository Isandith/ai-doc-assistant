from typing import List, Dict
from sqlalchemy.orm import Session
from app.models import Chunk
import re


class RetrievalService:
    """Service for retrieving relevant chunks using keyword search (BM25-style)"""
    
    @staticmethod
    def keyword_search(query: str, document_id: int, db: Session, top_k: int = 5) -> List[Dict[str, any]]:
        """
        Simple keyword-based retrieval.
        
        Args:
            query: User's question
            document_id: ID of the document to search
            db: Database session
            top_k: Number of top chunks to return
            
        Returns:
            List of relevant chunks with page numbers and scores
        """
        # Get all chunks for the document
        chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
        
        if not chunks:
            return []
        
        # Extract keywords from query (simple approach)
        query_keywords = RetrievalService._extract_keywords(query.lower())
        
        # Score each chunk
        scored_chunks = []
        for chunk in chunks:
            score = RetrievalService._calculate_score(query_keywords, chunk.text.lower())
            scored_chunks.append({
                "chunk_id": chunk.id,
                "page_number": chunk.page_number,
                "text": chunk.text,
                "score": score,
                "token_count": chunk.token_count
            })
        
        # Sort by score (descending) and return top K
        scored_chunks.sort(key=lambda x: x["score"], reverse=True)
        return scored_chunks[:top_k]
    
    @staticmethod
    def _extract_keywords(text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common stop words (simple list)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
            'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these',
            'those', 'what', 'which', 'who', 'when', 'where', 'why', 'how'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter stop words and short words
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        return keywords
    
    @staticmethod
    def _calculate_score(query_keywords: List[str], chunk_text: str) -> float:
        """Calculate relevance score based on keyword matching"""
        if not query_keywords:
            return 0.0
        
        score = 0.0
        chunk_words = chunk_text.lower().split()
        
        for keyword in query_keywords:
            # Count occurrences
            count = chunk_text.count(keyword)
            
            # TF (term frequency) - normalized by chunk length
            tf = count / max(len(chunk_words), 1)
            
            # Simple scoring (can be improved with IDF)
            score += tf * 10
        
        return score
    
    @staticmethod
    def format_sources_for_llm(chunks: List[Dict[str, any]]) -> tuple[str, Dict[int, int]]:
        """
        Format retrieved chunks as sources for LLM prompt.
        
        Returns:
            - Formatted source text with labels [S1], [S2], etc.
            - Mapping of source labels to page numbers
        """
        source_text = ""
        source_to_page = {}
        
        for idx, chunk in enumerate(chunks, 1):
            label = f"S{idx}"
            source_text += f"[{label}] (Page {chunk['page_number']})\n{chunk['text']}\n\n"
            source_to_page[idx] = chunk['page_number']
        
        return source_text, source_to_page
