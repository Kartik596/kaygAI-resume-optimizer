"""
PDF text extraction module
"""
import pdfplumber
import PyPDF2
from typing import List, Dict, Optional
from pathlib import Path
from src.utils.text_cleaner import TextCleaner

class PDFExtractor:
    """Extract text and metadata from PDF files"""
    
    def __init__(self, pdf_path: str):
        """Initialize PDF extractor"""
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        self.text_cleaner = TextCleaner()
        self._full_text: Optional[str] = None
        self._pages: Optional[List[str]] = None
        self._metadata: Optional[Dict] = None
    
    def extract_text(self, method: str = 'pdfplumber') -> str:
        """Extract all text from PDF"""
        if self._full_text is not None:
            return self._full_text
        
        if method == 'pdfplumber':
            self._full_text = self._extract_with_pdfplumber()
        elif method == 'pypdf2':
            self._full_text = self._extract_with_pypdf2()
        else:
            raise ValueError(f"Unknown extraction method: {method}")
        
        # Clean text
        self._full_text = self.text_cleaner.remove_page_numbers(self._full_text)
        self._full_text = self.text_cleaner.normalize_spacing(self._full_text)
        
        return self._full_text
    
    def _extract_with_pdfplumber(self) -> str:
        """Extract text using pdfplumber"""
        text_parts = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            raise RuntimeError(f"Error extracting PDF with pdfplumber: {e}")
        
        return '\n\n'.join(text_parts)
    
    def _extract_with_pypdf2(self) -> str:
        """Extract text using PyPDF2"""
        text_parts = []
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
        except Exception as e:
            raise RuntimeError(f"Error extracting PDF with PyPDF2: {e}")
        
        return '\n\n'.join(text_parts)
    
    def extract_pages(self) -> List[str]:
        """Extract text from each page separately"""
        if self._pages is not None:
            return self._pages
        
        self._pages = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        self._pages.append(
                            self.text_cleaner.normalize_spacing(page_text)
                        )
        except Exception as e:
            raise RuntimeError(f"Error extracting pages: {e}")
        
        return self._pages
    
    def extract_metadata(self) -> Dict:
        """Extract PDF metadata"""
        if self._metadata is not None:
            return self._metadata
        
        self._metadata = {}
        
        try:
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                info = pdf_reader.metadata
                
                if info:
                    self._metadata = {
                        'title': info.get('/Title', ''),
                        'author': info.get('/Author', ''),
                        'subject': info.get('/Subject', ''),
                        'creator': info.get('/Creator', ''),
                    }
                
                self._metadata['num_pages'] = len(pdf_reader.pages)
        except Exception as e:
            print(f"Warning: Could not extract metadata: {e}")
        
        return self._metadata
