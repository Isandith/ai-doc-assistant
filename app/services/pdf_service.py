import fitz  # PyMuPDF
from typing import List, Dict
import os


class PDFService:
    """Service for extracting text from PDF files page by page"""
    
    @staticmethod
    def extract_text_from_pdf(pdf_path: str) -> List[Dict[str, any]]:
        """
        Extract text from PDF page by page.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            List of dictionaries with page_number, text, and character_count
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        pages = []
        
        try:
            # Open PDF
            doc = fitz.open(pdf_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                
                pages.append({
                    "page_number": page_num + 1,  # 1-indexed
                    "text": text,
                    "character_count": len(text)
                })
            
            doc.close()
            
            return pages
        
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    @staticmethod
    def get_page_count(pdf_path: str) -> int:
        """Get the number of pages in a PDF"""
        try:
            doc = fitz.open(pdf_path)
            count = len(doc)
            doc.close()
            return count
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def validate_pdf(file_path: str) -> bool:
        """Validate if file is a valid PDF"""
        try:
            doc = fitz.open(file_path)
            doc.close()
            return True
        except:
            return False
