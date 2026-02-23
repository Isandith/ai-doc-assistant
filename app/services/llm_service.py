from typing import List, Dict, Tuple
from app.core.gemini_client import client
from app.core.config import DEFAULT_MODEL
import re


class LLMService:
    """Service for calling LLM API (Gemini) to answer questions with citations"""
    
    def __init__(self):
        self.client = client
        self.model_name = DEFAULT_MODEL
    
    def answer_with_sources(
        self, 
        question: str, 
        source_text: str, 
        source_to_page: Dict[int, int]
    ) -> Tuple[str, List[Dict[str, any]]]:
        """
        Generate an answer using provided sources and extract citations.
        
        Args:
            question: User's question
            source_text: Formatted sources with labels [S1], [S2], etc.
            source_to_page: Mapping of source number to page number
            
        Returns:
            - Generated answer text
            - List of citations with page numbers and snippets
        """
        # Build the prompt
        prompt = self._build_prompt(question, source_text)
        
        try:
            # Call Gemini API
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            answer = response.text
            
            # Parse citations from the answer
            citations = self._parse_citations(answer, source_text, source_to_page)
            
            return answer, citations
        
        except Exception as e:
            raise Exception(f"LLM API error: {str(e)}")
    
    def _build_prompt(self, question: str, source_text: str) -> str:
        """Build the prompt for the LLM"""
        prompt = f"""You are a helpful assistant that answers questions based ONLY on the provided source documents. 

IMPORTANT RULES:
1. Answer using ONLY information from the sources below
2. Cite sources using [S1], [S2], etc. format
3. If the sources don't contain the answer, say "I cannot find this information in the provided document"
4. Be concise and direct
5. Always include citations for factual claims

SOURCES:
{source_text}

QUESTION: {question}

ANSWER (with citations):"""
        
        return prompt
    
    def _parse_citations(
        self, 
        answer: str, 
        source_text: str,
        source_to_page: Dict[int, int]
    ) -> List[Dict[str, any]]:
        """
        Extract citation references from the answer and map to pages.
        
        Looks for patterns like [S1], [S2], etc. in the answer
        """
        citations = []
        
        # Find all source references in the answer
        citation_pattern = r'\[S(\d+)\]'
        matches = re.findall(citation_pattern, answer)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_matches = []
        for match in matches:
            if match not in seen:
                seen.add(match)
                unique_matches.append(match)
        
        # Map source numbers to pages and extract snippets
        for source_num_str in unique_matches:
            source_num = int(source_num_str)
            
            if source_num in source_to_page:
                page_number = source_to_page[source_num]
                
                # Extract snippet from source text
                snippet = self._extract_snippet(source_text, source_num)
                
                citations.append({
                    "page": page_number,
                    "snippet": snippet,
                    "source_label": f"S{source_num}"
                })
        
        return citations
    
    def _extract_snippet(self, source_text: str, source_num: int, max_length: int = 200) -> str:
        """Extract a snippet from the source text for a given source number"""
        # Find the source section
        pattern = rf'\[S{source_num}\][^\n]*\n(.+?)(?=\n\[S|\Z)'
        match = re.search(pattern, source_text, re.DOTALL)
        
        if match:
            full_text = match.group(1).strip()
            
            # Truncate if too long
            if len(full_text) > max_length:
                return full_text[:max_length] + "..."
            return full_text
        
        return "Source text not found"
